import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from ichiro.features import hourly, quarter_hourly
from ichiro.rules import SETUPS, Signal, signals
from ichiro.sim import Simulator

TAKER = 0.00035
SCORED_START = int(datetime(2026, 2, 1, tzinfo=UTC).timestamp() * 1000)
SCORED_END = int(datetime(2026, 11, 15, tzinfo=UTC).timestamp() * 1000)
HOLDOUT_FRAC = 0.20
TRIALS = [("S1", False), ("S1", True), ("S3", False), ("S3", True), ("S4", False), ("S4", True)]
PASS_R, PASS_N = 0.10, 100


def split_points(start=SCORED_START, end=SCORED_END):
    cut = start + int((end - start) * (1 - HOLDOUT_FRAC))
    folds = [start + int((cut - start) * k / 3) for k in range(4)]
    return folds, cut


class HoldoutLock:
    def __init__(self, path):
        self.path = Path(path)

    def acquire(self, version):
        if self.path.exists():
            raise RuntimeError(f"holdout for {version} already read at {self.path.read_text().strip()}")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(datetime.now(UTC).isoformat() + "\n")


def cost_side(book):
    return TAKER + book["half_spread"] + book["tick_frac"]


def load(manifest_path, root="."):
    m = json.loads(Path(manifest_path).read_text())
    raw = {}
    for f in m["files"]:
        raw.setdefault(f["symbol"], {})[f["kind"]] = pd.read_parquet(Path(root) / f["path"])
    costs = {b["symbol"]: cost_side(b) for b in m["books"]}
    data = {}
    for s, k in raw.items():
        h = hourly(k["candles_1h"], k["funding"])
        q = quarter_hourly(k["candles_15m"], h)
        data[s] = {"1h": h.reset_index(drop=True), "15m": q.reset_index(drop=True), "funding": k["funding"]}
    return data, costs


def bootstrap_ci(r, n=10_000, seed=7):
    if len(r) < 2:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    means = rng.choice(r, size=(n, len(r)), replace=True).mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def max_drawdown(equity):
    if len(equity) == 0:
        return 0.0
    e = np.concatenate([[10_000.0], equity])
    return float((e / np.maximum.accumulate(e) - 1).min())


def longest_losing(r):
    best = cur = 0
    for x in r:
        cur = cur + 1 if x < 0 else 0
        best = max(best, cur)
    return best


def metrics(t, span_ms):
    if t.empty:
        return {"n": 0}
    r = t["r"].to_numpy()
    lo, hi = bootstrap_ci(r)
    eq = t["equity_after"].to_numpy()
    start_eq = eq[0] - t["pnl"].iat[0]
    ret = eq[-1] / start_eq - 1
    dd = max_drawdown(eq * 10_000 / start_eq)
    return {
        "n": int(len(r)), "win_rate": float((r > 0).mean()), "expectancy_r": float(r.mean()),
        "ci_low": lo, "ci_high": hi, "total_r": float(r.sum()), "cost_r": float(t["cost_r"].mean()),
        "return": float(ret), "max_dd": dd, "ret_over_dd": float(ret / -dd) if dd < 0 else float("nan"),
        "longest_losing": longest_losing(r),
        "exposure": float((t["exit_ms"] - t["entry_ms"]).sum() / span_ms),
    }


def verdict(hold):
    n = hold.get("n", 0)
    if n == 0:
        return "INCONCLUSIVE"
    if hold["expectancy_r"] <= 0:
        return "FAIL"
    if n < PASS_N:
        return "INCONCLUSIVE"
    return "PASS" if hold["expectancy_r"] >= PASS_R and hold["ci_low"] > 0 else "FAIL"


def frames_for(data, tf):
    return {s: d[tf] for s, d in data.items()}


def run_trial(data, costs, name, h4):
    setup = SETUPS[name]
    frames = frames_for(data, setup.timeframe)
    sigs = {s: signals(name, f, h4) for s, f in frames.items()}
    sim = Simulator(setup, frames, costs, {s: d["funding"] for s, d in data.items()})
    trades = pd.DataFrame(sim.run(sigs, SCORED_START, SCORED_END))
    return trades, sigs, sim


def baseline(data, costs, name, h4, trades, sigs, seed=11):
    setup = SETUPS[name]
    frames = frames_for(data, setup.timeframe)
    rng = np.random.default_rng(seed)
    if trades.empty:
        return pd.DataFrame()
    atr_mult = []
    for s, lst in sigs.items():
        f = frames[s]
        for g in lst:
            a = f["atr"].iat[g.i]
            if a > 0:
                atr_mult.append(abs(f["close"].iat[g.i] - g.stop) / a)
    k = float(np.median(atr_mult))
    target_r = None
    if name == "S4":
        rs = [abs(g.target - frames[s]["close"].iat[g.i]) / abs(frames[s]["close"].iat[g.i] - g.stop)
              for s, lst in sigs.items() for g in lst]
        target_r = float(np.median(rs))
    n = sum(len(x) for x in sigs.values())
    out = {}
    markets = list(frames)
    for _ in range(n):
        s = markets[rng.integers(len(markets))]
        f = frames[s]
        idx = np.flatnonzero((f["time_ms"].to_numpy() >= SCORED_START) & (f["time_ms"].to_numpy() < SCORED_END) & f["ready"].to_numpy())
        i = int(rng.choice(idx))
        side = int(rng.choice([1, -1]))
        c, a = f["close"].iat[i], f["atr"].iat[i]
        stop = c - side * k * a
        tgt = c + side * target_r * k * a if target_r else None
        mid = None
        out.setdefault(s, {})[i] = Signal(i, side, float(stop), target=tgt, mid=mid)
    sim = Simulator(setup, frames, costs, {s: d["funding"] for s, d in data.items()})
    return pd.DataFrame(sim.run({s: list(v.values()) for s, v in out.items()}, SCORED_START, SCORED_END))


def segment(t, lo, hi):
    return t[(t["entry_ms"] >= lo) & (t["entry_ms"] < hi)] if not t.empty else t


def fmt(m):
    if m.get("n", 0) == 0:
        return "| 0 | | | | | | | | |"
    return (f"| {m['n']} | {m['win_rate']:.1%} | {m['expectancy_r']:+.3f} | [{m['ci_low']:+.3f}, {m['ci_high']:+.3f}] | "
            f"{m['total_r']:+.1f} | {m['cost_r']:.3f} | {m['return']:+.2%} | {m['max_dd']:.2%} | {m['longest_losing']} |")


def iso(ms):
    return datetime.fromtimestamp(ms / 1000, UTC).strftime("%Y-%m-%d %H:%M")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="v0.1")
    ap.add_argument("--manifest", default="data/manifests/phoenix-v0.1.json")
    ap.add_argument("--out", default="strategies/backtests")
    A = ap.parse_args()
    out = Path(A.out) / A.version / "2026-11-15-phoenix-majors"
    HoldoutLock(out / "holdout.lock").acquire(A.version)
    data, costs = load(A.manifest)
    folds, cut = split_points()
    summary = []
    lines = [f"# Backtest {A.version}: Phoenix SOL, BTC, ETH", "",
             f"Run: {datetime.now(UTC).isoformat()}. Manifest: `{A.manifest}`. Scored span {iso(SCORED_START)} to {iso(SCORED_END)} UTC.",
             f"Development folds start at {', '.join(iso(x) for x in folds[:3])}. Holdout starts {iso(cut)}. The holdout was read once, in this run.",
             "Cost per side: " + ", ".join(f"{s} {c * 1e4:.2f} bp" for s, c in costs.items()) + ", plus hourly Phoenix funding.", ""]
    for trial_no, (name, h4) in enumerate(TRIALS, 1):
        trades, sigs, sim = run_trial(data, costs, name, h4)
        label = f"{name} H4 {'on' if h4 else 'off'}"
        tdir = out / f"trial-{trial_no}-{name}-h4{'on' if h4 else 'off'}"
        tdir.mkdir(parents=True, exist_ok=True)
        trades.to_csv(tdir / "trades.csv", index=False)
        base = baseline(data, costs, name, h4, trades, sigs)
        rows = []
        for k in range(3):
            rows.append((f"dev fold {k + 1}", metrics(segment(trades, folds[k], folds[k + 1]), folds[k + 1] - folds[k])))
        hold = metrics(segment(trades, cut, SCORED_END), SCORED_END - cut)
        rows.append(("**holdout**", hold))
        rows.append(("baseline holdout", metrics(segment(base, cut, SCORED_END), SCORED_END - cut)))
        rows.append(("baseline all", metrics(base, SCORED_END - SCORED_START)))
        v = verdict(hold)
        nsig = sum(len(x) for x in sigs.values())
        skipped = pd.Series([d.get("reason") for d in sim.decisions if d["action"] != "enter"]).value_counts().to_dict()
        summary.append({"trial": trial_no, "setup": label, "verdict": v, "holdout": hold, "signals": nsig})
        lines += [f"## Trial {trial_no}: {label}: **{v}**", "",
                  f"Signals {nsig}. Trades {len(trades)}. Skipped decisions: {skipped or 'none'}.", "",
                  "| Segment | n | Win | Exp R | 95% CI | Total R | Cost R | Return | Max DD | Max loss streak |",
                  "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        lines += [f"| {seg} {fmt(m)}" for seg, m in rows]
        if not trades.empty:
            lines += ["", "Exit reasons (all): " + ", ".join(f"{k} {v}" for k, v in trades["exit_reason"].value_counts().items()),
                      "By market (holdout): " + ", ".join(
                          f"{s} n={len(g)} exp={g['r'].mean():+.3f}" for s, g in segment(trades, cut, SCORED_END).groupby("market"))]
        lines.append("")
    (out / "report.md").write_text("\n".join(lines) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, indent=1, default=float) + "\n")
    for s in summary:
        h = s["holdout"]
        print(s["trial"], s["setup"], s["verdict"], h.get("n"), round(h.get("expectancy_r", float("nan")), 3) if h.get("n") else "")


if __name__ == "__main__":
    main()

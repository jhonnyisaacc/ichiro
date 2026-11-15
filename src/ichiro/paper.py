import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

from ichiro import phoenix, trackb
from ichiro.backtest import cost_side
from ichiro.features import hourly, quarter_hourly
from ichiro.rules import SETUPS, signals
from ichiro.sim import Simulator

MARKETS = ["SOL", "BTC", "ETH"]
TRACK_A = {"A-S3-H4": ("S3", True), "A-S1-H4": ("S1", True)}
LABEL = "exploratory"
UPBIT = "https://api.upbit.com/v1/market/all"
FRAME_MS = {"15m": 900_000, "1h": 3_600_000}


def now_ms():
    return int(time.time() * 1000)


def iso(ms):
    return datetime.fromtimestamp(ms / 1000, UTC).strftime("%Y-%m-%d %H:%M")


class Store:
    def __init__(self, root):
        self.root = Path(root)
        self.state_path = self.root / "state" / "paper.json"
        self.journal_dir = self.root / "journal"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.journal_dir.mkdir(parents=True, exist_ok=True)
        self.state = json.loads(self.state_path.read_text()) if self.state_path.exists() else {}

    def save(self):
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, indent=1))
        tmp.replace(self.state_path)

    def written(self):
        return set(self.state.setdefault("written", []))

    def write(self, rows):
        seen = self.written()
        new = [r for r in rows if r["id"] not in seen]
        for r in new:
            path = self.journal_dir / f"{datetime.fromtimestamp(r['ts_ms'] / 1000, UTC):%Y-%m}.jsonl"
            with path.open("a") as fh:
                fh.write(json.dumps(r, default=float) + "\n")
            self.state["written"].append(r["id"])
        return len(new)


def init(store):
    s = store.state
    if "start_ms" in s:
        return
    s["start_ms"] = now_ms()
    s["costs"] = {m: cost_side(phoenix.book(m)) for m in MARKETS}
    s["upbit_known"] = sorted(trackb.new_krw_markets(requests.get(UPBIT, timeout=15).json(), [])[1])
    s["trackb_events"] = []
    s["written"] = []
    store.save()


def closed(df, step, t):
    return df[df["time_ms"] + step <= t].reset_index(drop=True)


def market_frames(t, start_ms):
    out = {}
    for m in MARKETS:
        h = closed(phoenix.candles(m, "1h", start_ms=start_ms - 1_000 * 3_600_000), FRAME_MS["1h"], t)
        q = closed(phoenix.candles(m, "15m", start_ms=start_ms - 500 * 900_000), FRAME_MS["15m"], t)
        f = phoenix.funding(m, start_ms - 60 * 86_400_000, t)
        hf = hourly(h, f)
        out[m] = {"1h": hf, "15m": quarter_hourly(q, hf), "funding": f}
    return out


def track_a(store, data, t):
    rows, status = [], {}
    for track, (name, h4) in TRACK_A.items():
        setup = SETUPS[name]
        frames = {m: d[setup.timeframe] for m, d in data.items()}
        stale = [m for m, f in frames.items() if int(f["close_ms"].iat[-1]) < t - 2 * FRAME_MS[setup.timeframe]]
        sigs = {m: ([] if m in stale else signals(name, f, h4)) for m, f in frames.items()}
        sim = Simulator(setup, frames, store.state["costs"], {m: d["funding"] for m, d in data.items()})
        trades = sim.run(sigs, store.state["start_ms"], t, close_at_end=False)
        for m, f in frames.items():
            fired = {s.i for s in sigs[m]}
            window = f[(f["close_ms"] >= store.state["start_ms"]) & (f["close_ms"] <= t)]
            for i, bar in window.iterrows():
                if i in fired:
                    continue
                ms = int(bar["close_ms"])
                regime = "hot" if bar["hot"] else {1: "trend_up", -1: "trend_down"}.get(int(bar["trend"]), "range")
                rows.append({"id": f"{track}:{m}:{ms}:bar", "event": "decision", "ts_ms": ms, "ts": iso(ms),
                             "mode": "paper", "label": LABEL, "track": track, "setup": name, "market": m,
                             "action": "no_trade", "reason": "stale" if m in stale else "no_setup",
                             "regime": regime, "close": float(bar["close"]), "strategy_version": "v0.1"})
        for d in sim.decisions:
            rows.append({"id": f"{track}:{d['market']}:{d['ms']}:{d['action']}", "event": "decision",
                         "ts_ms": d["ms"], "ts": iso(d["ms"]), "mode": "paper", "label": LABEL, "track": track,
                         "setup": name, "market": d["market"], "action": d["action"],
                         "direction": {1: "long", -1: "short"}.get(d.get("side")), "reason": d.get("reason"),
                         "invalidation": d.get("stop"), "risk_frac": 0.005,
                         "strategy_version": "v0.1"})
        for tr in trades:
            rows.append({"id": f"{track}:{tr['market']}:{tr['entry_ms']}:review", "event": "review",
                         "ts_ms": tr["exit_ms"], "ts": iso(tr["exit_ms"]), "mode": "paper", "label": LABEL,
                         "track": track, "market": tr["market"], "exit_reason": tr["exit_reason"],
                         "r_multiple": tr["r"], "cost_r": tr["cost_r"], "pnl": tr["pnl"],
                         "entry": tr["entry"], "entry_ts": iso(tr["entry_ms"]), "strategy_version": "v0.1"})
        p = sim.pos
        status[track] = {
            "equity": sim.equity, "trades": len(trades), "stale": stale,
            "open": None if p is None else {"market": p.market, "side": p.side, "entry": p.entry, "stop": p.stop,
                                            "entry_ts": iso(p.entry_ms), "leverage": round(p.leverage, 2)},
            "pending": None if sim.pending is None else sim.pending[0],
            "paused_until": iso(sim.pause_until) if sim.pause_until > t else None,
            "blocked_until": iso(sim.block_until) if sim.block_until > t else None,
            "today_r": sum(x["r"] for x in trades if x["exit_ms"] // 86_400_000 == t // 86_400_000),
        }
    return rows, status


def track_b(store, t, phoenix_markets):
    s = store.state
    try:
        markets = requests.get(UPBIT, timeout=15).json()
    except requests.RequestException:
        markets = None
    rows = []
    if markets:
        new, krw = trackb.new_krw_markets(markets, s["upbit_known"])
        s["upbit_known"] = sorted(set(s["upbit_known"]) | krw)
        for sym in new:
            ph = trackb.phoenix_symbol(sym, phoenix_markets)
            ev = {"upbit": sym, "phoenix": ph, "open_ms": t, "book": phoenix.book(ph) if ph else None}
            ev["action"] = "skip" if ph is None or not trackb.depth_ok(ev["book"]) else "enter"
            ev["reason"] = "not_on_phoenix" if ph is None else (None if ev["action"] == "enter" else "depth")
            s["trackb_events"].append(ev)
            rows.append({"id": f"B:{sym}:{t}:decision", "event": "decision", "ts_ms": t, "ts": iso(t),
                         "mode": "paper", "label": LABEL, "track": "B-upbit-open-short", "market": ph or sym,
                         "action": ev["action"], "direction": "short", "reason": ev["reason"],
                         "thesis": "Upbit KRW open; frozen ~/coins rule: 24h short, +20% stop"})
    status = []
    for ev in s["trackb_events"]:
        if ev["action"] != "enter":
            continue
        c = phoenix.candles(ev["phoenix"], "1m", start_ms=ev["open_ms"] - 60_000)
        f = phoenix.funding(ev["phoenix"], ev["open_ms"] - 3_600_000, t)
        o = trackb.outcome(ev["open_ms"], c, f, cost_side(ev["book"]), now_ms=t)
        status.append({"market": ev["phoenix"], **o})
        if o["status"] == "closed":
            rows.append({"id": f"B:{ev['upbit']}:{ev['open_ms']}:review", "event": "review", "ts_ms": o["exit_ms"],
                         "ts": iso(o["exit_ms"]), "mode": "paper", "label": LABEL, "track": "B-upbit-open-short",
                         "market": ev["phoenix"], "exit_reason": o["exit_reason"], "r_multiple": o["r"],
                         "ret": o["ret"], "entry": o["entry"]})
    return rows, status


def cycle(store):
    t = now_ms()
    data = market_frames(t, store.state["start_ms"])
    rows_a, status_a = track_a(store, data, t)
    rows_b, status_b = track_b(store, t, set(phoenix.markets()))
    n = store.write(rows_a + rows_b)
    store.state["last_cycle"] = {"ts": iso(t), "ms": t, "track_a": status_a, "track_b": status_b, "new_rows": n}
    store.save()
    return store.state["last_cycle"]


def run(root, interval):
    store = Store(root)
    init(store)
    while True:
        try:
            c = cycle(store)
            print(f"{c['ts']} new_rows={c['new_rows']}", flush=True)
        except Exception as exc:
            print(f"{iso(now_ms())} cycle_error {type(exc).__name__}: {exc}", flush=True)
        time.sleep(interval)


def status(root):
    store = Store(root)
    s = store.state
    if "last_cycle" not in s:
        print("no cycle yet")
        return
    c = s["last_cycle"]
    print(f"paper since {iso(s['start_ms'])} UTC, last cycle {c['ts']} UTC, label {LABEL}")
    for track, st in c["track_a"].items():
        print(f"{track}: equity ${st['equity']:,.2f}, trades {st['trades']}, today {st['today_r']:+.2f}R, "
              f"open {st['open']}, pending {st['pending']}, paused {st['paused_until']}, "
              f"loss-stop {st['blocked_until']}, stale {st['stale'] or 'none'}")
    print(f"B-upbit-open-short: {len(s.get('trackb_events', []))} listings seen, positions {c['track_b'] or 'none'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["run", "status", "once"])
    ap.add_argument("--root", default=".")
    ap.add_argument("--interval", type=int, default=60)
    A = ap.parse_args()
    if A.command == "run":
        run(A.root, A.interval)
    elif A.command == "once":
        store = Store(A.root)
        init(store)
        print(json.dumps(cycle(store), indent=1, default=float))
    else:
        status(A.root)


if __name__ == "__main__":
    main()

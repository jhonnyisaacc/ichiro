from dataclasses import dataclass

import numpy as np

from ichiro.features import base_pass, h4_pass


@dataclass(frozen=True)
class Signal:
    i: int
    side: int
    stop: float
    target: float | None = None
    mid: float | None = None


@dataclass(frozen=True)
class Setup:
    name: str
    timeframe: str
    track: str
    tp1_r: float | None
    tp1_frac: float
    tp2_r: float | None
    trail_atr: float | None
    hold_ms: int
    leverage_cap: float


HOUR = 3_600_000
SETUPS = {
    "S1": Setup("S1", "15m", "scalp", 1.0, 0.5, 2.0, None, 4 * HOUR, 5.0),
    "S3": Setup("S3", "1h", "swing", 1.5, 0.5, None, 2.0, 72 * HOUR, 3.0),
    "S4": Setup("S4", "1h", "swing", None, 1.0, None, None, 24 * HOUR, 3.0),
}


def allowed(f, h4):
    ok = f["ready"].to_numpy() & base_pass(f).to_numpy()
    if h4:
        ok &= h4_pass(f).fillna(False).to_numpy()
    return ok


def s1(f, h4):
    o, h, l, c = (f[k].to_numpy() for k in ("open", "high", "low", "close"))
    low20, high20, a = f["low20"].to_numpy(), f["high20"].to_numpy(), f["atr"].to_numpy()
    regime_ok = (f["hot"].fillna(False).to_numpy().astype(bool)) | (f["trend"].to_numpy() == 0)
    ok = allowed(f, h4) & regime_ok
    body = np.abs(c - o)
    lower = np.minimum(o, c) - l
    upper = h - np.maximum(o, c)
    wick_long = np.where(body > 0, lower >= 2 * body, lower > 0)
    wick_short = np.where(body > 0, upper >= 2 * body, upper > 0)
    long_ = ok & (l < low20) & (c > low20) & wick_long
    short = ok & (h > high20) & (c < high20) & wick_short
    mid = (low20 + high20) / 2
    out = []
    for i in np.flatnonzero(long_ | short):
        side = 1 if long_[i] else -1
        stop = l[i] - 0.25 * a[i] if side == 1 else h[i] + 0.25 * a[i]
        out.append(Signal(int(i), side, float(stop), mid=float(mid[i])))
    return out


def s3(f, h4):
    h, l, c = (f[k].to_numpy() for k in ("high", "low", "close"))
    e20, a, trend = f["ema20"].to_numpy(), f["atr"].to_numpy(), f["trend"].to_numpy()
    fr, p90, p10 = (f[k].to_numpy() for k in ("funding_8h", "funding_p90", "funding_p10"))
    ok = allowed(f, h4)
    out = []
    pull = {1: None, -1: None}
    for i in range(len(f)):
        for side in (1, -1):
            p = pull[side]
            if p is not None and i - p > 6:
                pull[side] = p = None
            if p is not None and i > p and trend[i] == side and ok[i]:
                broke = c[i] > h[p] if side == 1 else c[i] < l[p]
                crowded = (fr[i] > p90[i]) if side == 1 else (fr[i] < p10[i])
                if broke and not crowded:
                    stop = l[p] - 0.5 * a[i] if side == 1 else h[p] + 0.5 * a[i]
                    out.append(Signal(i, side, float(stop)))
                    pull[side] = None
                    continue
            touched = (l[i] <= e20[i] < c[i]) if side == 1 else (h[i] >= e20[i] > c[i])
            if trend[i] == side and touched:
                pull[side] = i
    return out


def s4(f, h4):
    l, h, c = (f[k].to_numpy() for k in ("low", "high", "close"))
    m, sd, r, a, trend = (f[k].to_numpy() for k in ("mean50", "std50", "rsi", "atr", "trend"))
    ok = allowed(f, h4) & (trend == 0)
    out = []
    for i in range(3, len(f)):
        if not ok[i]:
            continue
        z_prev = (c[i - 1] - m[i - 1]) / sd[i - 1]
        if z_prev <= -2.5 and r[i - 1] < 20 and c[i] > m[i] - 2.0 * sd[i]:
            out.append(Signal(i, 1, float(l[i - 2:i + 1].min() - 0.5 * a[i]), target=float(m[i])))
        elif z_prev >= 2.5 and r[i - 1] > 80 and c[i] < m[i] + 2.0 * sd[i]:
            out.append(Signal(i, -1, float(h[i - 2:i + 1].max() + 0.5 * a[i]), target=float(m[i])))
    return out


GENERATORS = {"S1": s1, "S3": s3, "S4": s4}


def signals(name, f, h4):
    return GENERATORS[name](f, h4)


def size(equity, risk_frac, entry, stop, cost_side, leverage_cap):
    stop_dist = abs(entry - stop) / entry
    if stop_dist <= 0:
        return None
    notional = equity * risk_frac / (stop_dist + 2 * cost_side)
    notional = min(notional, leverage_cap * equity)
    leverage = notional / equity
    if 0.5 / leverage < 3 * stop_dist:
        return None
    return {"notional": notional, "leverage": leverage, "stop_dist": stop_dist,
            "risk_usd": notional * (stop_dist + 2 * cost_side)}


def targets(setup, sig, entry):
    r = abs(entry - sig.stop)
    side = sig.side
    if setup.name == "S4":
        if (sig.target - entry) * side <= 0:
            return None
        return [(sig.target, 1.0)]
    tp1 = entry + side * setup.tp1_r * r
    if setup.tp2_r is None:
        return [(tp1, setup.tp1_frac)]
    two_r = entry + side * setup.tp2_r * r
    tp2 = two_r
    if sig.mid is not None and (sig.mid - tp1) * side > 0 and abs(sig.mid - entry) < abs(two_r - entry):
        tp2 = sig.mid
    return [(tp1, setup.tp1_frac), (tp2, 1 - setup.tp1_frac)]

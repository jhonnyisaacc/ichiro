from dataclasses import dataclass, field

import numpy as np

from ichiro.rules import size, targets

DAY = 86_400_000
WEEK = 7 * DAY


@dataclass
class Limits:
    risk_frac: float = 0.005
    daily_stop: float = -0.02
    weekly_stop: float = -0.05
    dd_halt: float = -0.10
    dd_pause_ms: int = WEEK
    streak: int = 3
    streak_pause_ms: int = DAY
    entries_per_day: int = 4


@dataclass
class Position:
    market: str
    side: int
    entry: float
    stop: float
    stop0: float
    qty: float
    notional: float
    risk_usd: float
    leverage: float
    entry_ms: int
    targets: list
    cost_side: float
    signal_ms: int
    pnl: float = 0.0
    costs: float = 0.0
    funding: float = 0.0
    tp_hit: int = 0
    best_close: float = 0.0
    exit_next_open: str | None = None
    fills: list = field(default_factory=list)


def week_start(ms):
    days = ms // DAY
    return (days - (days + 3) % 7) * DAY


class Simulator:
    def __init__(self, setup, frames, costs, funding, limits=None, equity=10_000.0):
        self.setup = setup
        self.frames = frames
        self.costs = costs
        self.funding = funding
        self.limits = limits or Limits()
        self.equity = equity
        self.peak = equity
        self.pos = None
        self.pending = None
        self.trades = []
        self.decisions = []
        self.pause_until = 0
        self.block_until = 0
        self.streak = 0
        self.entries = {m: [] for m in frames}
        self.day = None
        self.day_equity = equity
        self.week = None
        self.week_equity = equity

    def close_part(self, p, price, frac, ms, reason):
        qty = p.qty * frac
        gross = qty * (price - p.entry) * p.side
        cost = qty * price * p.cost_side
        p.pnl += gross - cost
        p.costs += cost
        p.fills.append((ms, price, frac, reason))
        p.qty -= qty
        if p.qty <= 1e-12:
            self.finish(p, ms, reason)

    def finish(self, p, ms, reason):
        net = p.pnl - p.funding
        self.equity += net
        self.peak = max(self.peak, self.equity)
        r = net / p.risk_usd
        self.trades.append({
            "market": p.market, "side": p.side, "signal_ms": p.signal_ms, "entry_ms": p.entry_ms,
            "exit_ms": ms, "entry": p.entry, "stop0": p.stop0, "notional": p.notional,
            "leverage": p.leverage, "risk_usd": p.risk_usd, "pnl": net, "costs": p.costs,
            "funding": p.funding, "r": r, "cost_r": (p.costs + max(p.funding, 0)) / p.risk_usd,
            "exit_reason": reason, "tp_hit": p.tp_hit, "equity_after": self.equity,
        })
        self.streak = self.streak + 1 if net < 0 else 0
        if self.streak >= self.limits.streak:
            self.pause_until = max(self.pause_until, ms + self.limits.streak_pause_ms)
            self.streak = 0
        if self.equity <= self.peak * (1 + self.limits.dd_halt):
            self.pause_until = max(self.pause_until, ms + self.limits.dd_pause_ms)
            self.peak = self.equity
        self.pos = None

    def accrue_funding(self, p, start_ms, end_ms):
        f = self.funding.get(p.market)
        if f is None or f.empty:
            return
        t = f["time_ms"].to_numpy()
        lo, hi = np.searchsorted(t, start_ms, side="right"), np.searchsorted(t, end_ms, side="right")
        if hi > lo:
            price = p.entry
            p.funding += float(f["rate"].to_numpy()[lo:hi].sum()) * p.qty * price * p.side

    def roll_periods(self, ms):
        day = ms // DAY
        if day != self.day:
            self.day, self.day_equity = day, self.equity
        week = week_start(ms)
        if week != self.week:
            self.week, self.week_equity = week, self.equity

    def manage(self, m, row, f, i):
        p = self.pos
        o, h, l, c = row["open"], row["high"], row["low"], row["close"]
        t0, t1 = int(row["time_ms"]), int(row["close_ms"])
        if p.exit_next_open:
            self.close_part(p, o, 1.0, t0, p.exit_next_open)
            return
        self.accrue_funding(p, t0, t1)
        hit_stop = l <= p.stop if p.side == 1 else h >= p.stop
        if hit_stop:
            fill = min(p.stop, o) if p.side == 1 else max(p.stop, o)
            self.close_part(p, fill, 1.0, t0, "stop" if p.tp_hit == 0 else "stop_after_tp")
            return
        while p.tp_hit < len(p.targets):
            price, frac = p.targets[p.tp_hit]
            through = h > price if p.side == 1 else l < price
            if not through:
                break
            done = sum(fr for _, fr in p.targets[:p.tp_hit])
            share = min(1.0, frac / (1 - done))
            p.tp_hit += 1
            self.close_part(p, price, share, t0, f"tp{p.tp_hit}")
            if self.pos is None:
                return
            if p.tp_hit == 1:
                be = p.entry * (1 + 2 * p.cost_side * p.side)
                p.stop = max(p.stop, be) if p.side == 1 else min(p.stop, be)
        p.best_close = max(p.best_close, c) if p.side == 1 else min(p.best_close, c)
        if self.setup.trail_atr and p.tp_hit >= 1:
            trail = p.best_close - p.side * self.setup.trail_atr * f["atr"].iat[i]
            p.stop = max(p.stop, trail) if p.side == 1 else min(p.stop, trail)
        if t1 - p.entry_ms >= self.setup.hold_ms:
            p.exit_next_open = "time"
        elif p.funding > 0.3 * p.risk_usd:
            p.exit_next_open = "funding"
        unreal = p.qty * (c - p.entry) * p.side - p.funding + p.pnl
        if self.equity + unreal <= self.day_equity * (1 + self.limits.daily_stop):
            p.exit_next_open = "daily_stop"
            self.block_until = max(self.block_until, (t1 // DAY + 1) * DAY)
        elif self.equity + unreal <= self.week_equity * (1 + self.limits.weekly_stop):
            p.exit_next_open = "weekly_stop"
            self.block_until = max(self.block_until, week_start(t1) + WEEK)

    def can_enter(self, m, ms):
        if self.pos is not None or self.pending is not None:
            return "position_open"
        if ms < self.pause_until:
            return "paused"
        if ms < self.block_until:
            return "loss_stop"
        if self.equity <= self.day_equity * (1 + self.limits.daily_stop):
            self.block_until = (ms // DAY + 1) * DAY
            return "loss_stop"
        if self.equity <= self.week_equity * (1 + self.limits.weekly_stop):
            self.block_until = week_start(ms) + WEEK
            return "loss_stop"
        recent = [t for t in self.entries[m] if t > ms - DAY]
        self.entries[m] = recent
        if len(recent) >= self.limits.entries_per_day:
            return "trade_budget"
        return None

    def open(self, m, sig, row, signal_ms):
        entry = float(row["open"])
        cost = self.costs[m]
        if (entry - sig.stop) * sig.side <= 0:
            return "stop_through_entry"
        sz = size(self.equity, self.limits.risk_frac, entry, sig.stop, cost, self.setup.leverage_cap)
        if sz is None:
            return "liquidation_distance"
        tg = targets(self.setup, sig, entry)
        if tg is None:
            return "target_behind_entry"
        qty = sz["notional"] / entry
        t0 = int(row["time_ms"])
        p = Position(m, sig.side, entry, sig.stop, sig.stop, qty, sz["notional"], sz["risk_usd"],
                     sz["leverage"], t0, tg, cost, signal_ms, best_close=entry)
        p.costs += sz["notional"] * cost
        p.pnl -= sz["notional"] * cost
        self.pos = p
        self.entries[m].append(t0)
        return None

    def run(self, signals_by_market, start_ms, end_ms, close_at_end=True):
        events = []
        for m, f in self.frames.items():
            sig_at = {s.i: s for s in signals_by_market.get(m, [])}
            times = f["time_ms"].to_numpy()
            for i in np.flatnonzero((times >= start_ms) & (times < end_ms)):
                events.append((int(times[i]), m, int(i), sig_at.get(int(i))))
        events.sort(key=lambda e: (e[0], e[1]))
        for t, m, i, sig in events:
            f = self.frames[m]
            row = f.iloc[i]
            self.roll_periods(t)
            if self.pending and self.pending[0] == m:
                _, psig, sig_ms = self.pending
                self.pending = None
                why = self.open(m, psig, row, sig_ms)
                if why:
                    self.decisions.append({"ms": t, "market": m, "action": "skip", "reason": why})
            if self.pos is not None and self.pos.market == m:
                self.manage(m, row, f, i)
            if sig is not None:
                close_ms = int(row["close_ms"])
                why = self.can_enter(m, close_ms)
                if why is None and i + 1 < len(f):
                    self.pending = (m, sig, close_ms)
                    self.decisions.append({"ms": close_ms, "market": m, "action": "enter", "side": sig.side, "stop": sig.stop})
                else:
                    self.decisions.append({"ms": close_ms, "market": m, "action": "no_trade",
                                           "reason": why or "end_of_data"})
        if self.pos is not None and close_at_end:
            f = self.frames[self.pos.market]
            last = f[f["time_ms"] < end_ms].iloc[-1]
            self.close_part(self.pos, float(last["close"]), 1.0, int(last["close_ms"]), "end_of_data")
        return self.trades

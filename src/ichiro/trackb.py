import pandas as pd

MINUTE = 60_000
HOUR = 3_600_000
HOLD_MS = 24 * HOUR
STOP_FRAC = 0.20
NOTIONAL = 1_000.0
MIN_DEPTH_MULT = 2.0


def outcome(open_ms, candles_1m, funding, cost_side, now_ms=None):
    c = candles_1m.sort_values("time_ms").reset_index(drop=True)
    entry_bar_ms = (open_ms // MINUTE) * MINUTE + MINUTE
    entry_rows = c[c["time_ms"] == entry_bar_ms]
    if entry_rows.empty:
        later = c[c["time_ms"] >= entry_bar_ms]
        if later.empty:
            return {"status": "waiting_for_entry_bar"}
        entry_rows = later.iloc[:1]
    e = entry_rows.iloc[0]
    entry = float(e["close"])
    entry_ms = int(e["time_ms"]) + MINUTE
    stop = entry * (1 + STOP_FRAC)
    qty = NOTIONAL / entry
    risk_usd = NOTIONAL * (STOP_FRAC + 2 * cost_side)
    path = c[(c["time_ms"] >= entry_ms) & (c["time_ms"] < entry_ms + HOLD_MS)]
    exit_price, exit_ms, reason = None, None, None
    for row in path.itertuples():
        if row.high >= stop:
            exit_price, exit_ms, reason = max(stop, row.open), int(row.time_ms), "stop"
            break
    done_at = entry_ms + HOLD_MS
    if reason is None:
        horizon = now_ms if now_ms is not None else int(c["time_ms"].max()) + MINUTE
        if horizon < done_at or path.empty:
            last = path.iloc[-1] if not path.empty else e
            return {"status": "open", "entry": entry, "entry_ms": entry_ms, "stop": stop,
                    "mark": float(last["close"]), "unrealized_pct": (entry - float(last["close"])) / entry}
        last = path.iloc[-1]
        exit_price, exit_ms, reason = float(last["close"]), int(last["time_ms"]) + MINUTE, "time"
    f = funding[(funding["time_ms"] > entry_ms) & (funding["time_ms"] <= exit_ms)] if funding is not None and not funding.empty else funding
    funding_paid = -float(f["rate"].sum()) * NOTIONAL if f is not None and not f.empty else 0.0
    costs = 2 * NOTIONAL * cost_side
    pnl = qty * (entry - exit_price) - costs - funding_paid
    return {"status": "closed", "entry": entry, "entry_ms": entry_ms, "stop": stop, "exit": exit_price,
            "exit_ms": exit_ms, "exit_reason": reason, "ret": pnl / NOTIONAL, "r": pnl / risk_usd,
            "funding_paid": funding_paid, "costs": costs}


def phoenix_symbol(upbit_symbol, phoenix_symbols):
    if upbit_symbol in phoenix_symbols:
        return upbit_symbol
    k = "k" + upbit_symbol
    return k if k in phoenix_symbols else None


def new_krw_markets(markets, known):
    krw = {m["market"].split("-", 1)[1] for m in markets if m["market"].startswith("KRW-")}
    return sorted(krw - set(known)), krw


def depth_ok(book, notional=NOTIONAL):
    return book["bid_depth_1pct_usd"] >= MIN_DEPTH_MULT * notional

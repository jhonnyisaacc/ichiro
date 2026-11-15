import sys
from datetime import UTC, datetime

import pandas as pd

from ichiro import phoenix, trackb
from ichiro.backtest import cost_side

EVENTS = ["H0084", "H0087", "H0137", "H0152", "H0168", "H0237", "H0288", "H0328", "H0349"]


def main(coins_root):
    ev = pd.read_parquet(f"{coins_root}/data/events.parquet").set_index("event_id").loc[EVENTS]
    tr = pd.read_csv(f"{coins_root}/analysis/a_short_open_trades.csv")
    tr = tr[(tr.entry == "open +0m") & (tr.hold_min == 1440) & (tr.stop == "+20%") & (tr["mode"] == "pessimistic")]
    ref = tr.set_index("event_id")
    listed = set(phoenix.markets())
    rows = []
    for eid, e in ev.iterrows():
        sym = trackb.phoenix_symbol(e.symbol, listed)
        open_ms = int(e.trading_open_ms)
        c = phoenix.candles(sym, "1m", start_ms=open_ms - 60_000, end_ms=open_ms + 25 * 3_600_000) if sym else pd.DataFrame()
        c = c[c.time_ms <= open_ms + 25 * 3_600_000] if len(c) else c
        f = phoenix.funding(sym, open_ms - 3_600_000, open_ms + 25 * 3_600_000) if sym else None
        o = trackb.outcome(open_ms, c, f, cost_side(phoenix.book(sym)), now_ms=open_ms + 26 * 3_600_000) if len(c) else {"status": "no_phoenix_data"}
        first = int(c.time_ms.min()) if len(c) else None
        vol = float(c[(c.time_ms >= open_ms) & (c.time_ms < open_ms + 86_400_000)].volumeQuote.sum()) if len(c) else 0.0
        b = ref.loc[eid] if eid in ref.index else None
        rows.append({
            "event": eid, "symbol": e.symbol, "open_utc": datetime.fromtimestamp(open_ms / 1000, UTC).strftime("%Y-%m-%d %H:%M"),
            "phoenix_first_bar_before_open": bool(first is not None and first <= open_ms),
            "phoenix_24h_volume_usd": round(vol), "phoenix_status": o["status"],
            "phoenix_ret": o.get("ret"), "phoenix_exit": o.get("exit_reason"),
            "binance_ret": None if b is None else float(b.ret), "binance_stopped": None if b is None else bool(b.stopped),
        })
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    df.to_csv(sys.stdout if len(sys.argv) < 3 else sys.argv[2], index=False)


if __name__ == "__main__":
    main(sys.argv[1])

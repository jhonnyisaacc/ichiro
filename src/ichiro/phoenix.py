import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

API = "https://perp-api.phoenix.trade"
FUNDING_START_MS = 1_761_955_200_000
FRAME_MS = {"1m": 60_000, "15m": 900_000, "1h": 3_600_000}
SESSION = requests.Session()
SESSION.headers["User-Agent"] = "ichiro-research/0.1"


def get(path, params=None, tries=4):
    for attempt in range(tries):
        r = SESSION.get(API + path, params=params, timeout=20)
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        return r.json()
    r.raise_for_status()


def markets():
    return {m["symbol"]: m for m in get("/v1/view/exchange/markets")}


def candles(symbol, timeframe, start_ms=None, end_ms=None):
    step = FRAME_MS[timeframe]
    end = end_ms or int(time.time() * 1000)
    rows = []
    while True:
        page = get(f"/v1/candles/{symbol}", {"timeframe": timeframe, "endTime": end, "limit": 2000})
        page = [c for c in page if start_ms is None or c["time"] >= start_ms]
        if not page:
            break
        rows += page
        earliest = min(c["time"] for c in page)
        if earliest >= end or len(page) < 2:
            break
        end = earliest - step
        time.sleep(0.15)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows).drop_duplicates("time").sort_values("time").reset_index(drop=True)
    df = df.rename(columns={"time": "time_ms"})
    return df[["time_ms", "open", "high", "low", "close", "markClose", "volume", "volumeQuote", "tradeCount"]]


def funding(symbol, start_ms, end_ms=None):
    end_ms = end_ms or int(time.time() * 1000)
    rows, lo = [], start_ms
    while lo < end_ms:
        hi = min(lo + 30 * 86_400_000, end_ms)
        rows += get(f"/v1/funding/{symbol}/rates", {"startTime": lo, "endTime": hi, "limit": 10000})["rates"]
        lo = hi
        time.sleep(0.15)
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["time_ms"] = (df["timestamp"] * 1000).astype("int64")
    df["rate"] = df["fundingRatePercentage"].astype(float) / 100
    return df[["time_ms", "rate"]].drop_duplicates("time_ms").sort_values("time_ms").reset_index(drop=True)


def book(symbol):
    b = get(f"/v1/view/orderbook/{symbol}")
    bid, ask = b["bids"][0][0], b["asks"][0][0]
    mid = (bid + ask) / 2
    prices = sorted({p for p, _ in b["bids"][:20]} | {p for p, _ in b["asks"][:20]})
    tick = min(round(b - a, 10) for a, b in zip(prices, prices[1:]) if b > a)
    depth = lambda side, lim: sum(p * q for p, q in b[side] if abs(p - mid) / mid <= lim)
    return {
        "symbol": symbol,
        "captured_ms": int(time.time() * 1000),
        "bid": bid,
        "ask": ask,
        "half_spread": (ask - bid) / 2 / mid,
        "tick": tick,
        "tick_frac": tick / mid,
        "bid_depth_1pct_usd": depth("bids", 0.01),
        "ask_depth_1pct_usd": depth("asks", 0.01),
    }


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gaps(times, step):
    return int((pd.Series(times).diff().dropna() > step).sum())


def fetch(symbols, timeframes, root="data"):
    root = Path(root)
    manifest = {"source": API, "fetched_at": datetime.now(UTC).isoformat(), "files": [], "books": []}
    for s in symbols:
        for tf in timeframes:
            df = candles(s, tf)
            path = root / "raw" / "phoenix" / "candles" / tf / f"{s}.parquet"
            path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(path, index=False)
            manifest["files"].append({
                "path": str(path), "symbol": s, "kind": f"candles_{tf}", "rows": len(df),
                "first_ms": int(df.time_ms.min()), "last_ms": int(df.time_ms.max()),
                "gaps": gaps(df.time_ms, FRAME_MS[tf]), "sha256": sha256(path),
            })
        f = funding(s, FUNDING_START_MS)
        path = root / "raw" / "phoenix" / "funding" / f"{s}.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        f.to_parquet(path, index=False)
        manifest["files"].append({
            "path": str(path), "symbol": s, "kind": "funding", "rows": len(f),
            "first_ms": int(f.time_ms.min()) if len(f) else None,
            "last_ms": int(f.time_ms.max()) if len(f) else None, "sha256": sha256(path),
        })
        manifest["books"].append(book(s))
    return manifest


if __name__ == "__main__":
    import sys

    syms = sys.argv[1:] or ["SOL", "BTC", "ETH"]
    m = fetch(syms, ["15m", "1h"])
    out = Path("data/manifests/phoenix-v0.1.json")
    out.write_text(json.dumps(m, indent=1) + "\n")
    for f in m["files"]:
        first = f["first_ms"] and datetime.fromtimestamp(f["first_ms"] / 1000, UTC).date()
        print(f["symbol"], f["kind"], f["rows"], first, f.get("gaps"))
    for b in m["books"]:
        print(b)

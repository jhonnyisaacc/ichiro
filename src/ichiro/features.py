import numpy as np
import pandas as pd

HOUR_MS = 3_600_000
WINDOW_30D_1H = 720


def wilder(series, n):
    return series.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def atr(df, n=14):
    prev = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - prev).abs(), (df["low"] - prev).abs()], axis=1).max(axis=1)
    return wilder(tr, n)


def rsi(close, n=14):
    delta = close.diff()
    up = wilder(delta.clip(lower=0), n)
    down = wilder(-delta.clip(upper=0), n)
    return 100 - 100 / (1 + up / down)


def ema(series, span):
    return series.ewm(span=span, adjust=False, min_periods=span).mean()


def trailing_pct(series, window):
    values = series.to_numpy(dtype=float)
    out = np.full(len(values), np.nan)
    for i in range(window, len(values)):
        past = values[i - window:i]
        past = past[~np.isnan(past)]
        if len(past) >= window // 2 and not np.isnan(values[i]):
            out[i] = (past < values[i]).mean()
    return pd.Series(out, index=series.index)


def trailing_quantile(series, window, q):
    return series.shift(1).rolling(window, min_periods=window // 2).quantile(q)


def trailing_z(series, window):
    past = series.shift(1).rolling(window, min_periods=window // 2)
    return (series - past.mean()) / past.std()


def funding_at(times_ms, funding):
    if funding is None or funding.empty:
        return pd.Series(np.nan, index=times_ms.index)
    idx = np.searchsorted(funding["time_ms"].to_numpy(), times_ms.to_numpy(), side="right") - 1
    rates = funding["rate"].to_numpy()
    return pd.Series(np.where(idx >= 0, rates[np.clip(idx, 0, None)], np.nan), index=times_ms.index)


def hourly(df, funding):
    f = df.copy()
    f["close_ms"] = f["time_ms"] + HOUR_MS
    f["atr"] = atr(f)
    f["ema20"] = ema(f["close"], 20)
    f["ema50"] = ema(f["close"], 50)
    f["rsi"] = rsi(f["close"])
    f["mean50"] = f["close"].rolling(50).mean()
    f["std50"] = f["close"].rolling(50).std()
    vol24 = f["volumeQuote"].rolling(24).sum()
    f["vol_z"] = trailing_z(vol24, WINDOW_30D_1H)
    rv = np.log(f["close"]).diff().rolling(24).std()
    f["rv_pct"] = trailing_pct(rv, WINDOW_30D_1H)
    f["atr_pct"] = trailing_pct(f["atr"] / f["close"], WINDOW_30D_1H)
    f["funding_8h"] = funding_at(f["close_ms"], funding) * 8
    f["funding_p90"] = trailing_quantile(f["funding_8h"], WINDOW_30D_1H, 0.9)
    f["funding_p10"] = trailing_quantile(f["funding_8h"], WINDOW_30D_1H, 0.1)
    four = f.set_index(pd.to_datetime(f["time_ms"], unit="ms"))["close"].resample("4h").agg(["last", "count"])
    four = four[four["count"] == 4]
    four_close = four["last"]
    four_ema = ema(four_close, 50)
    four_df = pd.DataFrame({
        "close_ms": (four.index - pd.Timestamp(0)) // pd.Timedelta(milliseconds=1) + 4 * HOUR_MS,
        "close4h": four_close.to_numpy(),
        "ema50_4h": four_ema.to_numpy(),
    }).dropna()
    f = pd.merge_asof(f.sort_values("close_ms"), four_df.sort_values("close_ms"), on="close_ms", direction="backward")
    up = (f["ema20"] > f["ema50"]) & (f["close4h"] > f["ema50_4h"])
    down = (f["ema20"] < f["ema50"]) & (f["close4h"] < f["ema50_4h"])
    f["trend"] = np.where(up, 1, np.where(down, -1, 0))
    f["hot"] = (f["vol_z"] >= 2.0) & (f["rv_pct"] >= 0.70)
    f["ready"] = f[["atr", "ema50", "mean50", "vol_z", "rv_pct", "atr_pct", "close4h"]].notna().all(axis=1)
    return f


REGIME_COLS = ["trend", "hot", "rv_pct", "atr_pct", "funding_8h", "funding_p90", "funding_p10", "ready"]


def quarter_hourly(df15, h):
    f = df15.copy()
    f["close_ms"] = f["time_ms"] + 900_000
    f["atr"] = atr(f)
    f["low20"] = f["low"].shift(1).rolling(20).min()
    f["high20"] = f["high"].shift(1).rolling(20).max()
    joined = h[["close_ms"] + REGIME_COLS].rename(columns={"close_ms": "h_close_ms"})
    f = pd.merge_asof(f.sort_values("close_ms"), joined.sort_values("h_close_ms"),
                      left_on="close_ms", right_on="h_close_ms", direction="backward")
    f["ready"] = f["ready"].fillna(False).astype(bool) & f[["atr", "low20"]].notna().all(axis=1)
    return f


def h4_pass(f):
    return (f["atr_pct"] >= 0.20) & (f["atr_pct"] <= 0.95) & (f["rv_pct"] >= 0.20)


def base_pass(f):
    return f["funding_8h"].abs() <= 0.001

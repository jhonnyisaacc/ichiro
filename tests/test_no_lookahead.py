import numpy as np
import pandas as pd

from ichiro.features import hourly, quarter_hourly
from ichiro.rules import signals
from tests.conftest import bars


def series(n, seed):
    rng = np.random.default_rng(seed)
    return 100 * np.exp(np.cumsum(0.006 * rng.standard_t(2.5, n)))


def test_hourly_features_do_not_use_future_bars():
    full = bars(series(1200, 1))
    funding = pd.DataFrame({"time_ms": full.time_ms, "rate": 0.00001})
    a = hourly(full, funding)
    b = hourly(full.iloc[:1000].reset_index(drop=True), funding)
    cols = ["atr", "ema20", "rsi", "vol_z", "rv_pct", "atr_pct", "trend", "funding_p90"]
    pd.testing.assert_frame_equal(a.loc[:998, cols].reset_index(drop=True), b.loc[:998, cols].reset_index(drop=True))


def test_signals_unchanged_when_future_is_cut():
    h_full = bars(series(1500, 8))
    q_full = bars(series(6000, 3), step=900_000)
    funding = pd.DataFrame({"time_ms": h_full.time_ms, "rate": 0.0})
    for name, tf in (("S1", "15m"), ("S3", "1h"), ("S4", "1h")):
        h = hourly(h_full, funding)
        h_cut = hourly(h_full.iloc[:1300].reset_index(drop=True), funding)
        f, f_cut = (h, h_cut) if tf == "1h" else (quarter_hourly(q_full, h), quarter_hourly(q_full.iloc[:5000].reset_index(drop=True), h_cut))
        limit = len(f_cut) - 1
        a = [s for s in signals(name, f, False) if s.i < limit]
        b = [s for s in signals(name, f_cut, False) if s.i < limit]
        assert a == b, name
        if name != "S4":
            assert len(a) > 0, name


def test_s4_fires_on_reversion_from_extreme_in_range():
    n = 60
    f = pd.DataFrame({
        "open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0,
        "mean50": 100.0, "std50": 1.0, "rsi": 50.0, "atr": 1.0, "trend": 0, "ready": True,
        "funding_8h": 0.0, "atr_pct": 0.5, "rv_pct": 0.5,
    }, index=range(n))
    f.loc[40, ["close", "low", "rsi"]] = [97.0, 96.8, 15.0]
    f.loc[41, ["close", "low"]] = [98.5, 97.9]
    sig = signals("S4", f, False)
    assert [(s.i, s.side, s.target) for s in sig] == [(41, 1, 100.0)]
    assert sig[0].stop == np.float64(96.8 - 0.5)

import numpy as np
import pandas as pd
import pytest

from ichiro.rules import Setup


def bars(prices, start_ms=1_767_225_600_000, step=3_600_000, spread=0.002):
    p = np.asarray(prices, dtype=float)
    o = np.concatenate([[p[0]], p[:-1]])
    return pd.DataFrame({
        "time_ms": start_ms + step * np.arange(len(p)),
        "open": o, "high": np.maximum(o, p) * (1 + spread), "low": np.minimum(o, p) * (1 - spread),
        "close": p, "markClose": p, "volume": 1.0, "volumeQuote": 1000.0 * np.exp(np.random.default_rng(len(p)).normal(0, 0.5, len(p))), "tradeCount": 10,
    })


@pytest.fixture
def setup_scalp():
    return Setup("S1", "15m", "scalp", 1.0, 0.5, 2.0, None, 4 * 3_600_000, 5.0)

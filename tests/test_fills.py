import pandas as pd
import pytest

from ichiro.rules import Signal
from ichiro.sim import Simulator


def frame(rows, step=900_000, start=1_767_225_600_000):
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close"])
    df["time_ms"] = start + step * df.index
    df["close_ms"] = df["time_ms"] + step
    df["atr"] = 1.0
    return df


def run(setup, rows, sig):
    f = frame(rows)
    sim = Simulator(setup, {"X": f}, {"X": 0.0}, {"X": pd.DataFrame(columns=["time_ms", "rate"])})
    return sim.run({"X": [sig]}, int(f.time_ms.iat[0]), int(f.time_ms.iat[-1]) + 900_000)


def test_stop_checked_before_target_in_same_bar(setup_scalp):
    rows = [[100, 100, 100, 100], [100, 103, 98, 101], [101, 101, 101, 101]]
    t = run(setup_scalp, rows, Signal(0, 1, 99.0, mid=110.0))
    assert t[0]["exit_reason"] == "stop"
    assert t[0]["r"] == pytest.approx(-1.0)


def test_gap_through_stop_fills_at_open(setup_scalp):
    rows = [[100, 100, 100, 100], [100, 100.5, 99.5, 100], [97, 97, 96, 96.5], [96, 96, 96, 96]]
    t = run(setup_scalp, rows, Signal(0, 1, 99.0, mid=110.0))
    assert t[0]["exit_reason"] == "stop"
    assert t[0]["r"] == pytest.approx(-3.0)


def test_target_needs_trade_through(setup_scalp):
    rows = [[100, 100, 100, 100], [100, 101, 99.5, 100.5], [100.5, 101.01, 100.2, 101], [101, 102.5, 100.9, 102.4]]
    t = run(setup_scalp, rows, Signal(0, 1, 99.0, mid=110.0))
    assert [f for f in t[0]["exit_reason"].split()] == ["tp2"]
    assert t[0]["r"] == pytest.approx(1.5)


def test_breakeven_after_tp1(setup_scalp):
    rows = [[100, 100, 100, 100], [100, 101.5, 99.8, 101], [101, 101, 99.9, 100], [100, 100, 100, 100]]
    t = run(setup_scalp, rows, Signal(0, 1, 99.0, mid=110.0))
    assert t[0]["exit_reason"] == "stop_after_tp"
    assert t[0]["r"] == pytest.approx(0.5)

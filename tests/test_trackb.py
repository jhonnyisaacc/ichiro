import pandas as pd
import pytest

from ichiro import trackb


def minutes(prices, start=1_790_000_000_000, highs=None):
    df = pd.DataFrame({"close": prices})
    df["time_ms"] = start + 60_000 * df.index
    df["open"] = df["close"].shift(1).fillna(df["close"])
    df["high"] = highs if highs is not None else df[["open", "close"]].max(axis=1)
    df["low"] = df[["open", "close"]].min(axis=1)
    return df


NOFUND = pd.DataFrame(columns=["time_ms", "rate"])


def test_short_profits_on_fall_after_24h():
    c = minutes([10.0, 10.0] + [9.0] * 1500)
    o = trackb.outcome(1_790_000_000_000, c, NOFUND, 0.0)
    assert o["status"] == "closed" and o["exit_reason"] == "time"
    assert o["ret"] == pytest.approx(0.10)
    assert o["r"] == pytest.approx(0.5)


def test_stop_fills_at_stop_without_gap():
    c = minutes([10.0, 10.0, 10.0, 13.0] + [13.0] * 1500)
    o = trackb.outcome(1_790_000_000_000, c, NOFUND, 0.0)
    assert o["exit"] == pytest.approx(12.0)


def test_stop_fills_pessimistically_on_gap():
    prices = [10.0, 10.0, 10.0, 13.0, 13.0] + [13.0] * 1500
    c = minutes(prices)
    c.loc[3, ["open", "high"]] = [13.0, 13.0]
    o = trackb.outcome(1_790_000_000_000, c, NOFUND, 0.0)
    assert o["exit_reason"] == "stop"
    assert o["exit"] == pytest.approx(13.0)
    assert o["ret"] == pytest.approx(-0.30)


def test_open_position_before_24h():
    c = minutes([10.0] * 100)
    o = trackb.outcome(1_790_000_000_000, c, NOFUND, 0.0, now_ms=1_790_000_000_000 + 100 * 60_000)
    assert o["status"] == "open"


def test_short_receives_positive_funding():
    c = minutes([10.0] * 1500)
    f = pd.DataFrame({"time_ms": [1_790_000_000_000 + 3_600_000 * k for k in range(1, 25)], "rate": 0.0001})
    o = trackb.outcome(1_790_000_000_000, c, f, 0.0)
    assert o["funding_paid"] < 0
    assert o["ret"] > 0


def test_symbol_mapping_and_new_markets():
    assert trackb.phoenix_symbol("PEPE", {"kPEPE"}) == "kPEPE"
    assert trackb.phoenix_symbol("HYPE", {"HYPE"}) == "HYPE"
    assert trackb.phoenix_symbol("XYZ", {"HYPE"}) is None
    new, krw = trackb.new_krw_markets([{"market": "KRW-A"}, {"market": "KRW-B"}, {"market": "BTC-C"}], ["A"])
    assert new == ["B"] and krw == {"A", "B"}

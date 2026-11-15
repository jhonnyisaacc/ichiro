import pytest

from ichiro.backtest import cost_side
from ichiro.rules import size


def test_journal_example_sizing():
    s = size(10_000, 0.005, 182.40, 181.10, 0.0, 5.0)
    assert s["notional"] == pytest.approx(7015.4, rel=1e-3)
    assert s["leverage"] == pytest.approx(0.70, abs=0.01)


def test_cost_included_in_risk():
    s = size(10_000, 0.005, 100.0, 99.0, 0.0005, 5.0)
    assert s["risk_usd"] == pytest.approx(50.0)
    assert s["notional"] == pytest.approx(50 / 0.011)


def test_leverage_cap_keeps_stop_and_shrinks_risk():
    s = size(10_000, 0.005, 100.0, 99.95, 0.0, 3.0)
    assert s["leverage"] == pytest.approx(3.0)
    assert s["risk_usd"] == pytest.approx(30_000 * 0.0005)


def test_liquidation_distance_rejects_wide_stop_at_high_leverage():
    assert size(10_000, 0.005, 100.0, 90.0, 0.0, 5.0) is not None
    assert size(10_000, 0.5, 100.0, 90.0, 0.0, 5.0) is None


def test_cost_model_adds_fee_spread_tick():
    assert cost_side({"half_spread": 0.0001, "tick_frac": 0.0002}) == pytest.approx(0.00065)

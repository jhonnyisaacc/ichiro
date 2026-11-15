import pytest

from ichiro.backtest import HoldoutLock, split_points


def test_holdout_read_once(tmp_path):
    lock = HoldoutLock(tmp_path / "holdout.lock")
    lock.acquire("v0.1")
    with pytest.raises(RuntimeError):
        lock.acquire("v0.1")


def test_holdout_is_last_twenty_percent():
    folds, cut = split_points(0, 1000)
    assert cut == 800
    assert folds == [0, 266, 533, 800]

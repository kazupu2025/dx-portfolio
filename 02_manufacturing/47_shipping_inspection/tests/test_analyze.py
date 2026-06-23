import pytest
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze, REQUIRED_COLUMNS


def make_df(pass_rate=0.98, n=50):
    """Helper to create test DataFrame with deterministic pass rate."""
    import numpy as np
    # Create deterministic results to ensure exact pass rate
    n_pass = int(n * pass_rate)
    results = ["合格"] * n_pass + ["不合格"] * (n - n_pass)
    holds = [0] * n_pass + [1] * (n - n_pass)
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=n, freq="D")[:n],
        "product": [f"製品{chr(65 + i % 4)}" for i in range(n)],
        "lot_id": [f"LOT-{i + 1:03d}" for i in range(n)],
        "result": results,
        "hold_flag": holds,
    })


def test_returns_dict():
    """Test that analyze returns a dictionary."""
    assert isinstance(analyze(make_df()), dict)


def test_required_keys():
    """Test that result contains all required keys."""
    r = analyze(make_df())
    for k in ["weekly_df", "product_df", "total", "pass_rate", "hold_count", "verdict"]:
        assert k in r


def test_verdict_good():
    """Test verdict is 'good' when pass rate >= 98%."""
    assert analyze(make_df(0.99))["verdict"] == "good"


def test_verdict_warning():
    """Test verdict is 'warning' when pass rate >= 95% and < 98%."""
    assert analyze(make_df(0.96))["verdict"] == "warning"


def test_verdict_alert():
    """Test verdict is 'alert' when pass rate < 95%."""
    assert analyze(make_df(0.90))["verdict"] == "alert"


def test_pass_rate_range():
    """Test pass rate is in valid range [0, 100]."""
    r = analyze(make_df(0.95))
    assert 0 <= r["pass_rate"] <= 100


def test_hold_count_nonneg():
    """Test hold count is non-negative."""
    assert analyze(make_df())["hold_count"] >= 0


def test_weekly_df_not_empty():
    """Test weekly dataframe is not empty."""
    assert len(analyze(make_df())["weekly_df"]) > 0

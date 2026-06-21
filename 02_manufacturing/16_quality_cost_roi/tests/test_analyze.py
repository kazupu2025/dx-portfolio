"""C-71 analyze.py TDD — 8テスト。"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze  # noqa: E402


def _make_df(months, prevention, appraisal, failure):
    return pd.DataFrame({
        "month":            months,
        "prevention_cost":  prevention,
        "appraisal_cost":   appraisal,
        "failure_cost":     failure,
    })


def test_verdict_good():
    # delta=900, invest=500 → ROI=1.8 > 1.0
    df = _make_df(["2024-01", "2024-02"], [300, 300], [200, 200], [1000, 100])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert abs(result["latest_roi"] - 1.8) < 0.01


def test_verdict_warning():
    # delta=200, invest=500 → ROI=0.4
    df = _make_df(["2024-01", "2024-02"], [300, 300], [200, 200], [1000, 800])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 0 < result["latest_roi"] <= 1.0


def test_verdict_alert():
    # failure 増加 → ROI < 0
    df = _make_df(["2024-01", "2024-02"], [300, 300], [200, 200], [800, 1000])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["latest_roi"] < 0


def test_single_row_good():
    # failure_ratio = 200/1000 = 0.2 < 0.3
    df = _make_df(["2024-01"], [500], [300], [200])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["latest_roi"] is None
    assert abs(result["failure_ratio"] - 0.2) < 0.01


def test_single_row_alert():
    # failure_ratio = 600/900 ≈ 0.667 ≥ 0.5
    df = _make_df(["2024-01"], [200], [100], [600])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["latest_roi"] is None


def test_roi_series_length():
    df = _make_df(
        ["2024-01", "2024-02", "2024-03"],
        [300, 300, 300],
        [200, 200, 200],
        [1000, 800, 600],
    )
    result = analyze.run_analysis(df)
    assert len(result["roi_series"]) == 2


def test_output_keys():
    df = _make_df(["2024-01", "2024-02"], [300, 300], [200, 200], [1000, 800])
    result = analyze.run_analysis(df)
    expected = {
        "roi_series", "latest_roi", "failure_ratio",
        "total_prevention", "total_appraisal", "total_failure",
        "n_months", "verdict",
    }
    assert expected == set(result.keys())


def test_missing_column_raises():
    df = pd.DataFrame({"month": ["2024-01"], "prevention_cost": [300]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)

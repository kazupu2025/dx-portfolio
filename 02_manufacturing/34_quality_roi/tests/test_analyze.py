"""C-88 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze


def _make_df(months, prevention, appraisal, internal, external):
    return pd.DataFrame({
        "month":            months,
        "prevention_cost":  prevention,
        "appraisal_cost":   appraisal,
        "internal_failure": internal,
        "external_failure": external,
    })


def test_verdict_good():
    """roi >= 100% → good（予防投資の1倍以上の失敗コスト削減）"""
    # first_failure=100, last_failure=0, total_prevention=100 → roi=100%
    df = _make_df(
        ["2024-01", "2024-02"],
        [50, 50], [0, 0],    # total_prevention=100
        [80, 0],  [20, 0],   # first_failure=100, last_failure=0 → roi=100%
    )
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["roi"] >= 100.0


def test_verdict_warning():
    """0 <= roi < 100% → warning"""
    # roi = (60-38)/520 * 100 ≈ 4.2%
    df = _make_df(
        ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"],
        [50, 52, 55, 55, 58, 60],
        [30, 30, 32, 32, 33, 33],
        [40, 38, 35, 32, 30, 28],
        [20, 18, 16, 14, 12, 10],
    )
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 0.0 <= result["roi"] < 100.0


def test_verdict_alert():
    """roi < 0% → alert（失敗コストが増加）"""
    # first_failure=10, last_failure=20 → roi < 0
    df = _make_df(
        ["2024-01", "2024-02"],
        [50, 50], [0, 0],
        [8, 16],  [2, 4],
    )
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["roi"] < 0.0


def test_verdict_warning_lower_boundary():
    """roi = 0.0% → warning（下限境界）"""
    # first_failure=last_failure → roi=0
    df = _make_df(
        ["2024-01", "2024-02"],
        [50, 50], [0, 0],
        [50, 50], [0, 0],
    )
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert result["roi"] == pytest.approx(0.0)


def test_avg_failure_ratio():
    """avg_failure_ratio の確認"""
    df = _make_df(
        ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"],
        [50, 52, 55, 55, 58, 60],
        [30, 30, 32, 32, 33, 33],
        [40, 38, 35, 32, 30, 28],
        [20, 18, 16, 14, 12, 10],
    )
    result = analyze.run_analysis(df)
    assert 0.0 < result["avg_failure_ratio"] < 100.0


def test_roi_calculation():
    """ROI計算値の検証: (first_failure - last_failure) / total_prevention * 100"""
    # total_prevention = (10+5)*2 = 30, first_failure=50, last_failure=20
    # roi = (50-20)/30*100 = 100%
    df = _make_df(
        ["2024-01", "2024-02"],
        [10, 10], [5, 5],
        [40, 16], [10, 4],
    )
    result = analyze.run_analysis(df)
    expected_roi = (50 - 20) / 30 * 100
    assert result["roi"] == pytest.approx(expected_roi, rel=1e-3)


def test_n_months():
    """n_months の確認"""
    df = _make_df(
        ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"],
        [50, 52, 55, 55, 58, 60],
        [30, 30, 32, 32, 33, 33],
        [40, 38, 35, 32, 30, 28],
        [20, 18, 16, 14, 12, 10],
    )
    result = analyze.run_analysis(df)
    assert result["n_months"] == 6


def test_missing_column_raises():
    """必須列不足で ValueError が発生する"""
    df = pd.DataFrame({"month": ["2024-01"], "prevention_cost": [50]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)

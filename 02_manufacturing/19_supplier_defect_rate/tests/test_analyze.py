"""C-73 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze  # noqa: E402


def _make_df(suppliers, months, incoming, defects):
    return pd.DataFrame({
        "supplier":    suppliers,
        "month":       months,
        "incoming_qty": incoming,
        "defect_qty":  defects,
    })


def test_verdict_good():
    # avg = 5/500 * 100 = 1.0% → good（境界値）
    df = _make_df(["A"], ["2024-01"], [500], [5])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["avg_defect_rate"] == pytest.approx(1.0)


def test_verdict_warning():
    # avg = 10/500 * 100 = 2.0% → warning
    df = _make_df(["A"], ["2024-01"], [500], [10])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 1.0 < result["avg_defect_rate"] <= 3.0


def test_verdict_alert():
    # avg = 20/500 * 100 = 4.0% → alert
    df = _make_df(["A"], ["2024-01"], [500], [20])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["avg_defect_rate"] > 3.0


def test_defect_rate_calculation():
    df = _make_df(["A"], ["2024-01"], [200], [4])
    result = analyze.run_analysis(df)
    assert result["result_df"]["defect_rate"].iloc[0] == pytest.approx(2.0)


def test_weighted_average():
    # A社: 100件 × 10% = 10不良, B社: 900件 × 1% = 9不良
    # 加重平均: 19/1000 * 100 = 1.9%（単純平均 5.5% とは異なる）
    df = _make_df(
        ["A", "B"], ["2024-01", "2024-01"],
        [100, 900], [10, 9],
    )
    result = analyze.run_analysis(df)
    assert result["avg_defect_rate"] == pytest.approx(1.9)


def test_worst_supplier():
    df = _make_df(
        ["A", "B", "C"], ["2024-01", "2024-01", "2024-01"],
        [500, 300, 800], [5, 15, 4],
    )
    result = analyze.run_analysis(df)
    # B社: 15/300 = 5.0%、A社: 1.0%、C社: 0.5%
    assert result["worst_supplier"] == "B"


def test_output_keys():
    df = _make_df(["A", "B"], ["2024-01", "2024-01"], [500, 300], [5, 9])
    result = analyze.run_analysis(df)
    expected = {"result_df", "avg_defect_rate", "worst_supplier",
                "best_supplier", "n_suppliers", "verdict"}
    assert set(result.keys()) == expected


def test_missing_column_raises():
    df = pd.DataFrame({"supplier": ["A"], "month": ["2024-01"]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)

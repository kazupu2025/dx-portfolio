"""C-75 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze  # noqa: E402


def _make_df(months, categories, amounts):
    return pd.DataFrame({
        "month":    months,
        "category": categories,
        "amount":   amounts,
    })


def test_verdict_good():
    # 内部損失20 + 外部損失10 = 30 / total=100 → ratio=30.0% → good（境界値）
    df = _make_df(
        ["2024-01", "2024-01", "2024-01", "2024-01"],
        ["予防コスト", "評価コスト", "内部損失コスト", "外部損失コスト"],
        [40, 30, 20, 10],
    )
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["failure_ratio"] == pytest.approx(30.0)


def test_verdict_warning():
    # ratio = 40% → warning
    df = _make_df(
        ["2024-01", "2024-01", "2024-01", "2024-01"],
        ["予防コスト", "評価コスト", "内部損失コスト", "外部損失コスト"],
        [30, 30, 25, 15],
    )
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 30.0 < result["failure_ratio"] <= 50.0


def test_verdict_alert():
    # ratio = 60% → alert
    df = _make_df(
        ["2024-01", "2024-01", "2024-01", "2024-01"],
        ["予防コスト", "評価コスト", "内部損失コスト", "外部損失コスト"],
        [20, 20, 40, 20],
    )
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["failure_ratio"] > 50.0


def test_verdict_warning_upper_boundary():
    # 内部損失30 + 外部損失20 = 50 / total=100 → ratio=50.0% → warning（上限境界値）
    df = _make_df(
        ["2024-01", "2024-01", "2024-01", "2024-01"],
        ["予防コスト", "評価コスト", "内部損失コスト", "外部損失コスト"],
        [30, 20, 30, 20],
    )
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert result["failure_ratio"] == pytest.approx(50.0)


def test_total_cost():
    # 100 + 200 + 300 + 400 = 1000
    df = _make_df(
        ["2024-01"] * 4,
        ["予防コスト", "評価コスト", "内部損失コスト", "外部損失コスト"],
        [100, 200, 300, 400],
    )
    result = analyze.run_analysis(df)
    assert result["total_cost"] == 1000


def test_cost_by_category():
    # 2ヶ月分: 評価コスト = 200 + 300 = 500
    df = _make_df(
        ["2024-01", "2024-01", "2024-02", "2024-02"],
        ["評価コスト", "予防コスト", "評価コスト", "予防コスト"],
        [200, 100, 300, 150],
    )
    result = analyze.run_analysis(df)
    assert result["cost_by_category"]["評価コスト"] == 500
    assert result["cost_by_category"]["予防コスト"] == 250


def test_dominant_category():
    # 評価コスト: 500 > 予防コスト: 250 → dominant = 評価コスト
    df = _make_df(
        ["2024-01", "2024-01", "2024-01", "2024-01"],
        ["予防コスト", "評価コスト", "内部損失コスト", "外部損失コスト"],
        [100, 500, 200, 200],
    )
    result = analyze.run_analysis(df)
    assert result["dominant_category"] == "評価コスト"


def test_missing_column_raises():
    df = pd.DataFrame({"month": ["2024-01"], "category": ["予防コスト"]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)

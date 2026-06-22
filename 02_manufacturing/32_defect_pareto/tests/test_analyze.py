"""C-86 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze


def _make_df(months, modes, counts):
    return pd.DataFrame({"month": months, "defect_mode": modes, "count": counts})


def test_verdict_good():
    """上位2モードが80%超 → top_pareto_count=2 → good"""
    df = _make_df(
        ["2024-01"]*3,
        ["A","B","C"],
        [70, 15, 15],  # A=70%, A+B=85% → pareto: A,B → count=2 → good
    )
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["top_pareto_count"] <= 2


def test_verdict_warning():
    """上位3〜4モードが80%超 → warning"""
    df = _make_df(
        ["2024-01"]*5,
        ["A","B","C","D","E"],
        [30, 25, 20, 15, 10],  # A=30%, A+B=55%, A+B+C=75%, A+B+C+D=90% → count=4 → warning
    )
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 3 <= result["top_pareto_count"] <= 4


def test_verdict_alert():
    """5モード以上が必要 → alert"""
    df = _make_df(
        ["2024-01"]*6,
        ["A","B","C","D","E","F"],
        [20,18,16,14,12,20],  # 均等分布 → 多くのモードが必要
    )
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["top_pareto_count"] >= 5


def test_verdict_good_boundary():
    """top_pareto_count=2 → good（境界値）"""
    df = _make_df(
        ["2024-01"]*3,
        ["A","B","C"],
        [60, 25, 15],  # A=60%, A+B=85% → count=2 → good
    )
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["top_pareto_count"] == 2


def test_top_mode():
    df = _make_df(
        ["2024-01","2024-01","2024-01"],
        ["寸法不良","外観傷","バリ"],
        [50, 30, 20],
    )
    result = analyze.run_analysis(df)
    assert result["top_mode"] == "寸法不良"


def test_pareto_df_columns():
    df = _make_df(["2024-01"],["A"],[10])
    result = analyze.run_analysis(df)
    expected = {"defect_mode","total","pct","cumulative_pct","pareto_flag"}
    assert expected.issubset(set(result["pareto_df"].columns))


def test_pareto_coverage_pct():
    """上位2モード: A=60,B=25 → 計85/100=85%"""
    df = _make_df(
        ["2024-01"]*3,
        ["A","B","C"],
        [60, 25, 15],
    )
    result = analyze.run_analysis(df)
    assert result["pareto_coverage_pct"] == pytest.approx(85.0)


def test_missing_column_raises():
    df = pd.DataFrame({"month": ["2024-01"], "defect_mode": ["A"]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)

"""C-93 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze


def _make_df(names, totals, certs):
    """テスト用DataFrameを生成。"""
    return pd.DataFrame(
        {
            "id": range(len(names)),
            "name": names,
            "category": ["部品"] * len(names),
            "period": ["2024-06"] * len(names),
            "quality_score": [80.0] * len(names),
            "delivery_score": [80.0] * len(names),
            "cost_score": [80.0] * len(names),
            "total_score": totals,
            "certification": certs,
        }
    )


def test_verdict_good():
    """avg_total_score >= 80 → "good"。"""
    df = _make_df(["A", "B"], [85.0, 90.0], ["認定", "認定"])
    result = analyze.run_analysis(df, pd.DataFrame())
    assert result["verdict"] == "good"


def test_verdict_warning():
    """60 <= avg_total_score < 80 → "warning"。"""
    df = _make_df(["A", "B"], [70.0, 65.0], ["条件付認定", "条件付認定"])
    result = analyze.run_analysis(df, pd.DataFrame())
    assert result["verdict"] == "warning"


def test_verdict_alert():
    """avg_total_score < 60 → "alert"。"""
    df = _make_df(["A", "B"], [50.0, 55.0], ["保留", "保留"])
    result = analyze.run_analysis(df, pd.DataFrame())
    assert result["verdict"] == "alert"


def test_verdict_good_boundary():
    """avg_total_score = 80.0 → "good"（境界値）。"""
    df = _make_df(["A"], [80.0], ["認定"])
    result = analyze.run_analysis(df, pd.DataFrame())
    assert result["verdict"] == "good"


def test_certified_count():
    """certification == "認定" の件数を正確にカウント。"""
    df = _make_df(["A", "B", "C"], [90.0, 75.0, 55.0], ["認定", "条件付認定", "保留"])
    result = analyze.run_analysis(df, pd.DataFrame())
    assert result["certified_count"] == 1


def test_avg_total_score():
    """avg_total_scoreは正確な平均値。"""
    df = _make_df(["A", "B"], [80.0, 60.0], ["認定", "条件付認定"])
    result = analyze.run_analysis(df, pd.DataFrame())
    assert result["avg_total_score"] == pytest.approx(70.0)


def test_top_supplier():
    """top_supplier は最高スコアのサプライヤー名。"""
    df = _make_df(["B", "A"], [90.0, 70.0], ["認定", "条件付認定"])
    result = analyze.run_analysis(df, pd.DataFrame())
    assert result["top_supplier"] == "B"


def test_empty_df():
    """空のDataFrame → デフォルト値を返す。"""
    result = analyze.run_analysis(pd.DataFrame(), pd.DataFrame())
    assert result["n_suppliers"] == 0

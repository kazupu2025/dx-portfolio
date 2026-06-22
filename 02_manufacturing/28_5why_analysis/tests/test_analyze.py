"""C-82 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze

def _make_df(months, cats, counts, recs):
    return pd.DataFrame({"month":months,"cause_category":cats,"count":counts,"recurrence":recs})

def test_verdict_good():
    # recurrence_rate = 1/10 = 10.0% → good（境界値）
    df = _make_df(["2024-01"],["設備要因"],[10],[1])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["recurrence_rate"] == pytest.approx(10.0)

def test_verdict_warning():
    # recurrence_rate = 2/10 = 20.0% → warning
    df = _make_df(["2024-01"],["設備要因"],[10],[2])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 10.0 < result["recurrence_rate"] <= 30.0

def test_verdict_alert():
    # recurrence_rate = 4/10 = 40.0% → alert
    df = _make_df(["2024-01"],["設備要因"],[10],[4])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["recurrence_rate"] > 30.0

def test_verdict_warning_upper_boundary():
    # recurrence_rate = 3/10 = 30.0% → warning（上限境界値）
    df = _make_df(["2024-01"],["設備要因"],[10],[3])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert result["recurrence_rate"] == pytest.approx(30.0)

def test_total_count():
    df = _make_df(["2024-01","2024-01"],["設備要因","材料要因"],[5,3],[1,0])
    result = analyze.run_analysis(df)
    assert result["total_count"] == 8

def test_recurrence_rate():
    # recurrence_rate = 3/20 = 15.0%
    df = _make_df(["2024-01","2024-01"],["設備要因","材料要因"],[10,10],[2,1])
    result = analyze.run_analysis(df)
    assert result["recurrence_rate"] == pytest.approx(15.0)

def test_top_cause_category():
    df = _make_df(["2024-01","2024-01"],["設備要因","材料要因"],[8,3],[1,0])
    result = analyze.run_analysis(df)
    assert result["top_cause_category"] == "設備要因"

def test_missing_column_raises():
    df = pd.DataFrame({"month":["2024-01"],"cause_category":["設備要因"]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)

"""C-80 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze

def _make_df(months, processes, codes, counts):
    return pd.DataFrame({"month": months, "process": processes, "defect_code": codes, "count": counts})

def test_verdict_good():
    df = _make_df(["2024-01"], ["切削工程"], ["D001"], [10])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["avg_monthly_count"] == pytest.approx(10.0)

def test_verdict_warning():
    df = _make_df(["2024-01"], ["切削工程"], ["D001"], [20])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 10.0 < result["avg_monthly_count"] <= 30.0

def test_verdict_alert():
    df = _make_df(["2024-01"], ["切削工程"], ["D001"], [40])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["avg_monthly_count"] > 30.0

def test_verdict_warning_upper_boundary():
    df = _make_df(["2024-01"], ["切削工程"], ["D001"], [30])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert result["avg_monthly_count"] == pytest.approx(30.0)

def test_total_count():
    df = _make_df(["2024-01","2024-01","2024-01"],["切削工程","溶接工程","組立工程"],["D001","D002","D003"],[5,3,2])
    result = analyze.run_analysis(df)
    assert result["total_count"] == 10

def test_top_process():
    df = _make_df(["2024-01","2024-01"],["切削工程","溶接工程"],["D001","D001"],[8,3])
    result = analyze.run_analysis(df)
    assert result["top_process"] == "切削工程"

def test_top_defect_code():
    df = _make_df(["2024-01","2024-01"],["切削工程","切削工程"],["D001","D002"],[7,2])
    result = analyze.run_analysis(df)
    assert result["top_defect_code"] == "D001"

def test_missing_column_raises():
    df = pd.DataFrame({"month": ["2024-01"], "process": ["切削工程"]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)

"""C-81 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze

def _make_df(months, inspectors, inspected, defects):
    return pd.DataFrame({"month":months,"inspector":inspectors,"inspected":inspected,"defects":defects})

def test_verdict_good():
    # defect_rate = 3/100 = 3.0% → good（境界値）
    df = _make_df(["2024-01"],["田中太郎"],[100],[3])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["overall_defect_rate"] == pytest.approx(3.0)

def test_verdict_warning():
    # defect_rate = 2/100 = 2.0% → warning
    df = _make_df(["2024-01"],["田中太郎"],[100],[2])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 1.0 <= result["overall_defect_rate"] < 3.0

def test_verdict_alert():
    # defect_rate = 0.5/100 = 0.5% → alert（見落とし疑い）
    df = _make_df(["2024-01"],["田中太郎"],[200],[1])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["overall_defect_rate"] < 1.0

def test_verdict_warning_lower_boundary():
    # defect_rate = 1/100 = 1.0% → warning（下限境界値）
    df = _make_df(["2024-01"],["田中太郎"],[100],[1])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert result["overall_defect_rate"] == pytest.approx(1.0)

def test_total_inspected():
    df = _make_df(["2024-01","2024-01"],["田中太郎","山田花子"],[100,80],[3,2])
    result = analyze.run_analysis(df)
    assert result["total_inspected"] == 180

def test_total_defects():
    df = _make_df(["2024-01","2024-01"],["田中太郎","山田花子"],[100,80],[3,2])
    result = analyze.run_analysis(df)
    assert result["total_defects"] == 5

def test_top_inspector():
    # 田中: 3/100=3% > 山田: 2/80=2.5%
    df = _make_df(["2024-01","2024-01"],["田中太郎","山田花子"],[100,80],[3,2])
    result = analyze.run_analysis(df)
    assert result["top_inspector"] == "田中太郎"

def test_missing_column_raises():
    df = pd.DataFrame({"month":["2024-01"],"inspector":["田中太郎"]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)

"""C-78 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze

def _make_df(months, change_types, counts):
    return pd.DataFrame({"month": months, "change_type": change_types, "count": counts})

def test_verdict_good():
    df = _make_df(["2024-01"], ["設備変更"], [5])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["avg_monthly_count"] == pytest.approx(5.0)

def test_verdict_warning():
    df = _make_df(["2024-01"], ["設備変更"], [8])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 5.0 < result["avg_monthly_count"] <= 15.0

def test_verdict_alert():
    df = _make_df(["2024-01"], ["設備変更"], [20])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["avg_monthly_count"] > 15.0

def test_verdict_warning_upper_boundary():
    df = _make_df(["2024-01"], ["設備変更"], [15])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert result["avg_monthly_count"] == pytest.approx(15.0)

def test_total_count():
    df = _make_df(["2024-01","2024-01","2024-01"],["人員変更","設備変更","材料変更"],[2,3,1])
    result = analyze.run_analysis(df)
    assert result["total_count"] == 6

def test_top_change_type():
    df = _make_df(["2024-01","2024-01","2024-01"],["人員変更","設備変更","設備変更"],[2,3,3])
    result = analyze.run_analysis(df)
    assert result["top_change_type"] == "設備変更"

def test_n_types():
    df = _make_df(["2024-01","2024-01","2024-01"],["人員変更","設備変更","材料変更"],[2,3,1])
    result = analyze.run_analysis(df)
    assert result["n_types"] == 3

def test_missing_column_raises():
    df = pd.DataFrame({"month": ["2024-01"], "change_type": ["設備変更"]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)

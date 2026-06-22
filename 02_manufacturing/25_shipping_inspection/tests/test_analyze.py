"""C-79 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze

def _make_df(months, inspected, passed, hold):
    return pd.DataFrame({"month":months,"inspected":inspected,"passed":passed,"hold_count":hold})

def test_verdict_good():
    # passed=99/inspected=100 → rate=99.0% → good（境界値）
    df = _make_df(["2024-01"],[100],[99],[1])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["pass_rate"] == pytest.approx(99.0)

def test_verdict_warning():
    # passed=97/100 → rate=97.0% → warning
    df = _make_df(["2024-01"],[100],[97],[2])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 95.0 <= result["pass_rate"] < 99.0

def test_verdict_alert():
    # passed=90/100 → rate=90.0% → alert
    df = _make_df(["2024-01"],[100],[90],[5])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["pass_rate"] < 95.0

def test_verdict_warning_lower_boundary():
    # passed=95/100 → rate=95.0% → warning（下限境界値）
    df = _make_df(["2024-01"],[100],[95],[3])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert result["pass_rate"] == pytest.approx(95.0)

def test_total_inspected():
    df = _make_df(["2024-01","2024-02"],[100,120],[98,118],[1,1])
    result = analyze.run_analysis(df)
    assert result["total_inspected"] == 220

def test_pass_rate():
    # passed=216/220 ≈ 98.18%
    df = _make_df(["2024-01","2024-02"],[100,120],[98,118],[1,1])
    result = analyze.run_analysis(df)
    assert result["pass_rate"] == pytest.approx(216/220*100)

def test_hold_count():
    df = _make_df(["2024-01","2024-02"],[100,120],[98,118],[3,5])
    result = analyze.run_analysis(df)
    assert result["total_hold"] == 8

def test_missing_column_raises():
    df = pd.DataFrame({"month":["2024-01"],"inspected":[100]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)

"""C-91 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze

def _make_df(rpn_list):
    return pd.DataFrame({
        "id": range(len(rpn_list)),
        "process_name": ["P"] * len(rpn_list),
        "failure_mode": ["F"] * len(rpn_list),
        "effect": ["E"] * len(rpn_list),
        "severity": [5] * len(rpn_list),
        "cause": ["C"] * len(rpn_list),
        "occurrence": [5] * len(rpn_list),
        "detection": [5] * len(rpn_list),
        "rpn": rpn_list,
        "current_control": [""] * len(rpn_list),
        "action_required": [""] * len(rpn_list),
        "created_at": ["2024-01-01"] * len(rpn_list),
        "updated_at": ["2024-01-01"] * len(rpn_list),
    })

def test_verdict_good():
    df = _make_df([50, 80, 100])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"

def test_verdict_warning():
    df = _make_df([150, 180, 200])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"

def test_verdict_alert():
    df = _make_df([250, 300, 350])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"

def test_verdict_good_boundary():
    """avg_rpn = 100.0 → good（境界値）"""
    df = _make_df([100, 100, 100])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["avg_rpn"] == pytest.approx(100.0)

def test_avg_rpn():
    df = _make_df([100, 200, 300])
    result = analyze.run_analysis(df)
    assert result["avg_rpn"] == pytest.approx(200.0)

def test_max_rpn():
    df = _make_df([100, 200, 400])
    result = analyze.run_analysis(df)
    assert result["max_rpn"] == 400

def test_high_risk_count():
    """RPN > 200 → high_risk"""
    df = _make_df([100, 250, 300])
    result = analyze.run_analysis(df)
    assert result["high_risk_count"] == 2

def test_empty_df():
    result = analyze.run_analysis(pd.DataFrame())
    assert result["n_items"] == 0
    assert result["verdict"] == "good"

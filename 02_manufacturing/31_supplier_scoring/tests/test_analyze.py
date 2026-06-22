"""C-85 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze


def _make_df(suppliers, defect_rates, cpks, claim_counts):
    return pd.DataFrame({
        "supplier":    suppliers,
        "defect_rate": defect_rates,
        "cpk":         cpks,
        "claim_count": claim_counts,
    })


def test_verdict_good():
    """avg_score ≥ 80 → good"""
    # 不良率0%, Cpk=1.67, クレーム0件 → 各スコア100 → total=100
    df = _make_df(["A"], [0.0], [1.67], [0])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["avg_total_score"] >= 80.0


def test_verdict_warning():
    """avg_score ≈ 62 → warning"""
    df = _make_df(["A"], [4.0], [1.0], [6])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 60.0 <= result["avg_total_score"] < 80.0


def test_verdict_alert():
    """avg_score < 60 → alert"""
    # 不良率10%, Cpk=0.5, クレーム20件 → 各スコア最低
    df = _make_df(["A"], [10.0], [0.5], [20])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["avg_total_score"] < 60.0


def test_verdict_good_boundary():
    """avg_score = 80.0 → good（境界値）"""
    # defect_score=80, cpk_score=80, claim_score=80 → total=80
    # defect_rate=2.0 → 100-2.0*10=80, cpk=1.336 → 1.336/1.67*100≈80, claim=4 → 100-4*5=80
    df = _make_df(["A"], [2.0], [1.336], [4])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["avg_total_score"] == pytest.approx(80.0, abs=1.0)


def test_best_supplier():
    df = _make_df(["A","B"], [0.5, 5.0], [1.5, 0.9], [1, 10])
    result = analyze.run_analysis(df)
    assert result["best_supplier"] == "A"


def test_worst_supplier():
    df = _make_df(["A","B"], [0.5, 5.0], [1.5, 0.9], [1, 10])
    result = analyze.run_analysis(df)
    assert result["worst_supplier"] == "B"


def test_n_suppliers():
    df = _make_df(["A","B","C"], [1.0, 2.0, 3.0], [1.4, 1.2, 1.0], [2, 4, 6])
    result = analyze.run_analysis(df)
    assert result["n_suppliers"] == 3


def test_missing_column_raises():
    df = pd.DataFrame({"supplier": ["A"], "defect_rate": [1.0]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)

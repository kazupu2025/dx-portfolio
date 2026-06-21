"""C-68 analyze.py TDD — 8テスト。"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze  # noqa: E402


def _make_df(ids, defect, delivery, price):
    return pd.DataFrame({
        "supplier_id":    ids,
        "defect_rate":    defect,
        "delivery_rate":  delivery,
        "price_variance": price,
    })


def test_verdict_good():
    # composite = 95*0.5 + 98*0.3 + 95*0.2 = 47.5+29.4+19 = 95.9 ≥ 80
    df = _make_df(["A"], [0.5], [98.0], [1.0])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["avg_score"] >= 80


def test_verdict_warning():
    # composite = 70*0.5 + 85*0.3 + 70*0.2 = 35+25.5+14 = 74.5
    df = _make_df(["A"], [3.0], [85.0], [6.0])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 60 <= result["avg_score"] < 80


def test_verdict_alert():
    # composite = 30*0.5 + 75*0.3 + 25*0.2 = 15+22.5+5 = 42.5 < 60
    df = _make_df(["A"], [7.0], [75.0], [15.0])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["avg_score"] < 60


def test_score_defect_conversion():
    assert analyze._score_defect(1.0) == 90.0
    assert analyze._score_defect(15.0) == 0.0   # clamped at 0


def test_score_delivery_conversion():
    assert analyze._score_delivery(95.0) == 95.0
    assert analyze._score_delivery(110.0) == 100.0  # clamped at 100


def test_score_price_conversion():
    assert analyze._score_price(10.0) == 50.0   # 100 - 10*5
    assert analyze._score_price(25.0) == 0.0    # clamped at 0


def test_output_keys():
    df = _make_df(["A", "B"], [1.0, 3.0], [95.0, 85.0], [2.0, 6.0])
    result = analyze.run_analysis(df)
    expected = {
        "scored_df", "avg_score", "best_supplier",
        "worst_supplier", "n_suppliers", "verdict",
    }
    assert expected == set(result.keys())


def test_missing_column_raises():
    df = pd.DataFrame({"supplier_id": ["A"], "defect_rate": [1.0]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)

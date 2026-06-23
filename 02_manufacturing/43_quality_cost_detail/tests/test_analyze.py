import pytest
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze, REQUIRED_COLUMNS

def make_df(failure_pct=20):
    months = ["2024-01", "2024-02"]
    rows = []
    for m in months:
        rows.append({"month": m, "cost_category": "予防コスト", "amount": 200000})
        rows.append({"month": m, "cost_category": "評価コスト", "amount": 200000})
        rows.append({"month": m, "cost_category": "内部失敗コスト", "amount": int(400000 * failure_pct / 100)})
        rows.append({"month": m, "cost_category": "外部失敗コスト", "amount": int(200000 * failure_pct / 100)})
    return pd.DataFrame(rows)

def test_returns_dict():
    assert isinstance(analyze(make_df()), dict)

def test_required_keys():
    r = analyze(make_df())
    for k in ["category_df","trend_df","total_cost","failure_ratio","verdict"]:
        assert k in r

def test_verdict_good():
    assert analyze(make_df(15))["verdict"] == "good"

def test_verdict_warning():
    assert analyze(make_df(40))["verdict"] == "warning"

def test_verdict_alert():
    assert analyze(make_df(80))["verdict"] == "alert"

def test_failure_ratio_range():
    r = analyze(make_df(20))
    assert 0 <= r["failure_ratio"] <= 100

def test_total_cost_positive():
    assert analyze(make_df())["total_cost"] > 0

def test_category_df_not_empty():
    assert len(analyze(make_df())["category_df"]) > 0

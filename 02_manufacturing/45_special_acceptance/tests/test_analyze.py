import pytest
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze, REQUIRED_COLUMNS

def make_df(per_month=5, n_months=2):
    rows = []
    for m in range(n_months):
        for i in range(per_month):
            rows.append({
                "date": f"2024-0{m+1}-{i+1:02d}",
                "lot_id": f"LOT-{m*per_month+i+1:03d}",
                "reason_category": ["寸法外れ","外観不良","強度不足","その他"][i%4],
                "approver": "品管部長",
                "quantity": (i+1)*10,
            })
    return pd.DataFrame(rows)

def test_returns_dict():
    assert isinstance(analyze(make_df()), dict)

def test_required_keys():
    r = analyze(make_df())
    for k in ["monthly_df","reason_df","total_count","avg_monthly","top_reason","verdict"]:
        assert k in r

def test_verdict_good():
    assert analyze(make_df(2))["verdict"] == "good"

def test_verdict_warning():
    assert analyze(make_df(7))["verdict"] == "warning"

def test_verdict_alert():
    assert analyze(make_df(12))["verdict"] == "alert"

def test_total_count():
    assert analyze(make_df(5,2))["total_count"] == 10

def test_reason_df_sorted():
    r = analyze(make_df())
    assert r["reason_df"]["count"].iloc[0] >= r["reason_df"]["count"].iloc[-1]

def test_avg_monthly_positive():
    assert analyze(make_df(5))["avg_monthly"] > 0

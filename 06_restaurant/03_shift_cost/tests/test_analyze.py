import pytest
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze, REQUIRED_COLUMNS

def make_df(n=10, hourly=1000, hours=8, sales=1500000):
    rows = []
    for i in range(n):
        rows.append({
            "date": f"2024-01-{(i%28)+1:02d}",
            "staff_name": ["田中","鈴木","佐藤"][i%3],
            "role": ["ホール","キッチン","レジ"][i%3],
            "start_time": "09:00",
            "end_time": f"{9+hours:02d}:00",
            "hourly_rate": hourly,
            "break_minutes": 60,
        })
    return pd.DataFrame(rows)

def test_returns_dict():
    assert isinstance(analyze(make_df()), dict)

def test_required_keys():
    r = analyze(make_df())
    for k in ["df","staff_df","role_df","daily_df","total_cost","total_hours","labor_ratio","verdict"]:
        assert k in r

def test_verdict_good():
    # 低コスト → 人件費率低い
    r = analyze(make_df(n=5, hourly=1000, hours=4), monthly_sales=5000000)
    assert r["verdict"] == "good"

def test_verdict_alert():
    # 高コスト → 人件費率高い
    r = analyze(make_df(n=30, hourly=1300, hours=8), monthly_sales=500000)
    assert r["verdict"] == "alert"

def test_total_cost_positive():
    assert analyze(make_df())["total_cost"] > 0

def test_labor_ratio_calc():
    r = analyze(make_df(n=1, hourly=1000, hours=8), monthly_sales=1000000)
    # 7時間 × 1000円 = 7000円 / 1000000 * 100 = 0.7%
    assert r["labor_ratio"] < 5

def test_staff_df_not_empty():
    assert len(analyze(make_df())["staff_df"]) > 0

def test_role_df_not_empty():
    assert len(analyze(make_df())["role_df"]) > 0

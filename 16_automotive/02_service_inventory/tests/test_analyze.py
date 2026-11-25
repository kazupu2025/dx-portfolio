import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze

def make_service_df(n=20, completion_pct=0.85):
    rows = []
    for i in range(n):
        status = "完了" if i < int(n * completion_pct) else "作業中"
        rows.append({
            "date": f"2024-0{(i%3)+1}-{(i%28)+1:02d}",
            "job_id": f"J{i+1:03d}",
            "customer": f"顧客{i+1}",
            "vehicle_type": ["軽自動車","普通車","SUV","トラック"][i%4],
            "service_type": ["定期点検","車検","修理","タイヤ交換","オイル交換"][i%5],
            "labor_hours": 1.0 + i%6,
            "parts_cost": 5000 * (i%8),
            "labor_rate": 8000,
            "status": status,
        })
    return pd.DataFrame(rows)

def make_parts_df(alert_count=2):
    rows = []
    for i in range(10):
        stock = 3 if i < alert_count else 20
        rows.append({
            "part_id": f"PR{i+1:03d}",
            "part_name": f"部品{i+1}",
            "category": ["オイル類","消耗品","タイヤ類","電装品"][i%4],
            "current_stock": stock,
            "min_stock": 10,
            "unit_cost": 5000,
            "supplier": f"仕入先{i%3+1}",
        })
    return pd.DataFrame(rows)

def test_returns_dict(): assert isinstance(analyze(make_service_df(), make_parts_df()), dict)
def test_required_keys():
    r = analyze(make_service_df(), make_parts_df())
    for k in ["service_df","service_type_df","vehicle_df","parts_df","alert_parts","total_revenue","completion_rate","stock_alert_count","verdict"]:
        assert k in r
def test_verdict_good(): assert analyze(make_service_df(completion_pct=0.90), make_parts_df(alert_count=1))["verdict"] == "good"
def test_verdict_warning(): assert analyze(make_service_df(completion_pct=0.65), make_parts_df(alert_count=5))["verdict"] == "warning"
def test_completion_rate_range():
    r = analyze(make_service_df(), make_parts_df())
    assert 0 <= r["completion_rate"] <= 100
def test_alert_parts_count():
    r = analyze(make_service_df(), make_parts_df(alert_count=3))
    assert r["stock_alert_count"] == 3
def test_total_revenue_positive(): assert analyze(make_service_df(), make_parts_df())["total_revenue"] > 0
def test_service_type_df_not_empty(): assert len(analyze(make_service_df(), make_parts_df())["service_type_df"]) > 0

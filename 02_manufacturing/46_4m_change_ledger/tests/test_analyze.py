import pytest
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze, REQUIRED_COLUMNS

def make_df(per_month=5, n_months=2):
    rows = []
    types = ["Man","Machine","Material","Method"]
    processes = ["切断工程","溶接工程","塗装工程","検査工程"]
    for m in range(n_months):
        for i in range(per_month):
            rows.append({
                "date": f"2024-0{m+1}-{i+1:02d}",
                "change_type": types[i%4],
                "process": processes[i%4],
                "description": f"変更{i+1}",
                "risk_level": ["低","中","高"][i%3],
            })
    return pd.DataFrame(rows)

def test_returns_dict():
    assert isinstance(analyze(make_df()), dict)

def test_required_keys():
    r = analyze(make_df())
    for k in ["monthly_df","type_df","process_df","total_count","high_risk_count","avg_monthly","verdict"]:
        assert k in r

def test_verdict_good():
    assert analyze(make_df(3))["verdict"] == "good"

def test_verdict_warning():
    assert analyze(make_df(10))["verdict"] == "warning"

def test_verdict_alert():
    assert analyze(make_df(20))["verdict"] == "alert"

def test_total_count():
    assert analyze(make_df(5,2))["total_count"] == 10

def test_high_risk_nonneg():
    assert analyze(make_df())["high_risk_count"] >= 0

def test_type_df_has_4m():
    r = analyze(make_df())
    assert len(r["type_df"]) <= 4

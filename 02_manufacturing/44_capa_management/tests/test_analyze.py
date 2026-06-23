import pytest
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze, REQUIRED_COLUMNS

def make_df(completion_rate=0.9, n=10):
    import numpy as np
    rows = []
    for i in range(n):
        open_d = pd.Timestamp("2024-01-01") + pd.Timedelta(days=i)
        due_d = open_d + pd.Timedelta(days=30)
        if i < int(n * completion_rate):
            close_d = due_d - pd.Timedelta(days=5)
        else:
            close_d = pd.NaT
        rows.append({
            "capa_id": f"CAPA-{i+1:03d}",
            "open_date": open_d.strftime("%Y-%m-%d"),
            "due_date": due_d.strftime("%Y-%m-%d"),
            "close_date": close_d.strftime("%Y-%m-%d") if not pd.isna(close_d) else "",
            "category": ["設備","工程","材料","人的ミス"][i%4],
        })
    return pd.DataFrame(rows)

def test_returns_dict():
    assert isinstance(analyze(make_df()), dict)

def test_required_keys():
    r = analyze(make_df())
    for k in ["total","completed","completion_rate","on_time_rate","overdue","category_df","verdict"]:
        assert k in r

def test_verdict_good():
    assert analyze(make_df(0.95))["verdict"] == "good"

def test_verdict_warning():
    assert analyze(make_df(0.75))["verdict"] == "warning"

def test_verdict_alert():
    assert analyze(make_df(0.5))["verdict"] == "alert"

def test_total_correct():
    assert analyze(make_df(n=10))["total"] == 10

def test_completion_rate_range():
    r = analyze(make_df(0.8))
    assert 0 <= r["completion_rate"] <= 100

def test_category_df_not_empty():
    assert len(analyze(make_df())["category_df"]) > 0

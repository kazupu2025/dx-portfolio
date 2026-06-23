import pytest
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze, REQUIRED_COLUMNS

def make_df(recurrence_rate=0.10, n=20):
    import numpy as np
    rng = np.random.default_rng(42)
    flags = rng.choice([0, 1], n, p=[1-recurrence_rate, recurrence_rate])
    categories = ["設備不良","作業ミス","材料不良","設計不良","管理不備"]
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=n, freq="D")[:n],
        "issue_id": [f"ISS-{i+1:03d}" for i in range(n)],
        "root_cause_category": [categories[i%5] for i in range(n)],
        "recurrence_flag": flags,
    })

def test_returns_dict():
    assert isinstance(analyze(make_df()), dict)

def test_required_keys():
    r = analyze(make_df())
    for k in ["category_df","monthly_df","total","recurrence_count","recurrence_rate","top_category","verdict"]:
        assert k in r

def test_verdict_good():
    assert analyze(make_df(0.03))["verdict"] == "good"

def test_verdict_warning():
    assert analyze(make_df(0.10))["verdict"] == "warning"

def test_verdict_alert():
    assert analyze(make_df(0.20))["verdict"] == "alert"

def test_total_correct():
    assert analyze(make_df(n=20))["total"] == 20

def test_recurrence_rate_range():
    r = analyze(make_df(0.10))
    assert 0 <= r["recurrence_rate"] <= 100

def test_category_df_not_empty():
    assert len(analyze(make_df())["category_df"]) > 0

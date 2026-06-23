import pytest
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze, REQUIRED_COLUMNS

def make_df(n_months=1, count_per_month=5):
    rows = []
    for m in range(n_months):
        for i in range(count_per_month):
            rows.append({
                "date": f"2024-0{m+1}-{i+1:02d}",
                "customer": f"顧客{chr(65+i%4)}",
                "category": ["寸法不良","外観不良","機能不良","包装不良"][i%4],
                "severity": ["軽微","中程度","重大"][i%3],
                "status": "完了" if i%2==0 else "対応中",
            })
    return pd.DataFrame(rows)

def test_returns_dict():
    assert isinstance(analyze(make_df()), dict)

def test_required_keys():
    r = analyze(make_df())
    for k in ["monthly_df","category_df","customer_df","total_count","open_count","avg_monthly","top_category","verdict"]:
        assert k in r

def test_verdict_good():
    assert analyze(make_df(2,3))["verdict"] == "good"

def test_verdict_warning():
    assert analyze(make_df(2,8))["verdict"] == "warning"

def test_verdict_alert():
    assert analyze(make_df(2,12))["verdict"] == "alert"

def test_total_count():
    assert analyze(make_df(2,5))["total_count"] == 10

def test_category_df_sorted():
    r = analyze(make_df())
    assert r["category_df"]["count"].is_monotonic_decreasing or len(r["category_df"]) == 1

def test_open_count_nonneg():
    assert analyze(make_df())["open_count"] >= 0

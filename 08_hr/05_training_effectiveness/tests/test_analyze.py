import pytest
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze, REQUIRED_COLUMNS

def make_df(improvement=20, n=10):
    rows = []
    for i in range(n):
        pre = 50
        post = pre + improvement + (i % 3)
        rows.append({
            "employee_id": f"E{i+1:03d}",
            "name": f"社員{i+1}",
            "department": ["営業","製造","総務","IT","経理"][i%5],
            "training_name": ["ビジネスマナー研修","Excel基礎","安全衛生","リーダーシップ","IT基礎"][i%5],
            "training_date": f"2024-01-{(i%28)+1:02d}",
            "pre_score": pre,
            "post_score": min(post, 100),
            "training_cost": 30000,
            "training_hours": 8,
        })
    return pd.DataFrame(rows)

def test_returns_dict(): assert isinstance(analyze(make_df()), dict)

def test_required_keys():
    r = analyze(make_df())
    for k in ["df","training_df","dept_df","avg_improvement","avg_improvement_rate","total_cost","total_participants","verdict"]:
        assert k in r

def test_verdict_good(): assert analyze(make_df(20))["verdict"] == "good"
def test_verdict_warning(): assert analyze(make_df(10))["verdict"] == "warning"
def test_verdict_alert(): assert analyze(make_df(5))["verdict"] == "alert"
def test_improvement_positive(): assert analyze(make_df(15))["avg_improvement"] > 0
def test_total_participants(): assert analyze(make_df(n=10))["total_participants"] == 10
def test_training_df_not_empty(): assert len(analyze(make_df())["training_df"]) > 0

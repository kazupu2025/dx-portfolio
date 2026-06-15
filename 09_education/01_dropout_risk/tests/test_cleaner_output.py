"""tests/test_cleaner_output.py — 14テスト"""
import pytest
import pandas as pd
from pathlib import Path
import yaml

BASE = Path(__file__).resolve().parent.parent
OUT  = BASE / "output"

@pytest.fixture(scope="module")
def config():
    with open(BASE / "config.yml", encoding="utf-8") as f:
        return yaml.safe_load(f)

@pytest.fixture(scope="module")
def df():
    p = OUT / "cleaned_dropout_202401.csv"
    if not p.exists():
        return None
    return pd.read_csv(p, encoding="utf-8-sig")

def test_csv_exists():
    assert (OUT / "cleaned_dropout_202401.csv").exists()

def test_row_count(df, config):
    assert df is not None
    assert config["min_rows"] <= len(df) <= config["max_rows"], f"row count: {len(df)}"

def test_required_columns(df):
    assert df is not None
    required = {"student_id","subject","attendance_rate","midterm_score","final_score",
                "assignment_rate","engagement_score","dropout_risk_score","risk_category"}
    missing = required - set(df.columns)
    assert len(missing) == 0, f"missing columns: {missing}"

def test_student_id_not_null(df):
    assert df is not None
    assert df["student_id"].isna().sum() == 0

def test_subject_not_null(df):
    assert df is not None
    assert df["subject"].isna().sum() == 0

def test_attendance_rate_not_null(df):
    assert df is not None
    assert df["attendance_rate"].isna().sum() == 0

def test_midterm_score_not_null(df):
    assert df is not None
    assert df["midterm_score"].isna().sum() == 0

def test_final_score_not_null(df):
    assert df is not None
    assert df["final_score"].isna().sum() == 0

def test_dropout_risk_score_not_null(df):
    assert df is not None
    assert df["dropout_risk_score"].isna().sum() == 0

def test_dropout_risk_score_range(df):
    assert df is not None
    assert df["dropout_risk_score"].between(0, 100).all(), \
        f"range: [{df['dropout_risk_score'].min()}, {df['dropout_risk_score'].max()}]"

def test_attendance_range(df):
    assert df is not None
    assert df["attendance_rate"].between(0, 100).all()

def test_risk_category_values(df):
    assert df is not None
    valid = {"高リスク", "中リスク", "低リスク"}
    actual = set(df["risk_category"].unique())
    assert actual.issubset(valid), f"unexpected: {actual - valid}"

def test_subject_count(df, config):
    assert df is not None
    n = df["subject"].nunique()
    assert n == config["expected_subject_count"], f"got {n} subjects"

def test_student_count(df, config):
    assert df is not None
    n = df["student_id"].nunique()
    assert n == config["expected_student_count"], f"got {n} students"

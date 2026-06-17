# -*- coding: utf-8 -*-
import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(BASE_DIR, "output", "cleaned_contracts_202401.csv")

REQUIRED_COLS = [
    "contract_date", "contract_id", "plan", "industry",
    "monthly_fee", "usage_months", "login_count", "support_count",
    "status", "churn_reason", "ltv", "is_churned",
    "churn_risk", "arpu_grade", "source_file"
]


@pytest.fixture(scope="module")
def df():
    assert os.path.exists(OUTPUT_FILE), f"Output file not found: {OUTPUT_FILE}"
    return pd.read_csv(OUTPUT_FILE, encoding="utf-8-sig")


def test_output_file_exists():
    assert os.path.exists(OUTPUT_FILE)


def test_row_count_at_least_420(df):
    assert len(df) >= 420, f"Row count {len(df)} < 420"


def test_required_columns_present(df):
    for col in REQUIRED_COLS:
        assert col in df.columns, f"Missing column: {col}"


def test_contract_date_format(df):
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    bad = df["contract_date"].dropna()[~df["contract_date"].dropna().str.match(pattern)]
    assert len(bad) == 0, f"Bad dates: {bad.head().tolist()}"


def test_monthly_fee_positive(df):
    fees = pd.to_numeric(df["monthly_fee"], errors="coerce")
    assert (fees > 0).all(), "monthly_fee has non-positive values"


def test_usage_months_at_least_1(df):
    months = pd.to_numeric(df["usage_months"], errors="coerce")
    assert (months >= 1).all(), "usage_months has values < 1"


def test_login_count_non_negative(df):
    counts = pd.to_numeric(df["login_count"], errors="coerce")
    assert (counts >= 0).all(), "login_count has negative values"


def test_ltv_positive(df):
    ltv = pd.to_numeric(df["ltv"], errors="coerce")
    assert (ltv > 0).all(), "ltv has non-positive values"


def test_is_churned_binary(df):
    vals = set(df["is_churned"].dropna().unique())
    assert vals.issubset({0, 1}), f"is_churned contains unexpected values: {vals}"


def test_churn_risk_three_categories(df):
    cats = set(df["churn_risk"].dropna().unique())
    assert cats == {"高リスク", "中リスク", "低リスク"}, f"Unexpected churn_risk values: {cats}"


def test_arpu_grade_two_categories(df):
    cats = set(df["arpu_grade"].dropna().unique())
    assert cats == {"高ARPU", "低ARPU"}, f"Unexpected arpu_grade values: {cats}"


def test_plan_three_categories(df):
    plans = set(df["plan"].dropna().unique())
    assert len(plans) == 3, f"Expected 3 plans, got {len(plans)}: {plans}"


def test_industry_five_categories(df):
    industries = set(df["industry"].dropna().unique())
    assert len(industries) == 5, f"Expected 5 industries, got {len(industries)}: {industries}"


def test_source_file_three_categories(df):
    sources = set(df["source_file"].dropna().unique())
    assert len(sources) == 3, f"Expected 3 source files, got {len(sources)}: {sources}"


def test_churn_count_positive(df):
    churn_count = int(df["is_churned"].sum())
    assert churn_count >= 1, f"No churned records found"


def test_missing_rate_acceptable(df):
    check_cols = [c for c in REQUIRED_COLS if c != "churn_reason"]
    missing_rate = df[check_cols].isnull().mean().max()
    assert missing_rate <= 0.15, f"Max missing rate {missing_rate:.1%} exceeds 15%"

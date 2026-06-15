"""
B-11 テスト: クレンジング出力検証（14テスト）
"""
import pytest
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent.parent
CSV_PATH = BASE / "output" / "cleaned_credit_202401.csv"

REQUIRED_COLS = [
    "application_id", "age", "occupation", "annual_income",
    "years_employed", "total_debt", "past_delays", "loan_amount",
    "loan_purpose", "credit_score", "risk_category",
    "debt_income_ratio", "loan_income_ratio", "score_imputed",
]

VALID_OCCUPATIONS = {"会社員", "公務員", "自営業", "パート・アルバイト", "無職"}
VALID_RISK_CATEGORIES = {"高リスク", "中リスク", "低リスク"}


@pytest.fixture(scope="module")
def df():
    assert CSV_PATH.exists(), f"クレンジング済みCSVが存在しません: {CSV_PATH}"
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def test_csv_exists():
    assert CSV_PATH.exists(), f"CSV not found: {CSV_PATH}"


def test_row_count(df):
    assert 300 <= len(df) <= 2000, f"行数が範囲外: {len(df)}"


def test_required_columns(df):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    assert missing == [], f"不足列: {missing}"


def test_application_id_no_null(df):
    assert df["application_id"].isnull().sum() == 0


def test_age_no_null(df):
    assert df["age"].isnull().sum() == 0


def test_occupation_no_null(df):
    assert df["occupation"].isnull().sum() == 0


def test_annual_income_no_null(df):
    assert df["annual_income"].isnull().sum() == 0


def test_credit_score_range(df):
    assert df["credit_score"].between(0, 100).all(), (
        f"スコア範囲外: min={df['credit_score'].min()}, max={df['credit_score'].max()}"
    )


def test_risk_category_values(df):
    invalid = set(df["risk_category"].unique()) - VALID_RISK_CATEGORIES
    assert invalid == set(), f"不正なリスク分類値: {invalid}"


def test_annual_income_nonneg(df):
    assert (df["annual_income"] >= 0).all()


def test_total_debt_nonneg(df):
    assert (df["total_debt"] >= 0).all()


def test_past_delays_nonneg(df):
    assert (df["past_delays"] >= 0).all()


def test_debt_income_ratio_nonneg(df):
    assert (df["debt_income_ratio"] >= 0).all()


def test_occupation_five_types(df):
    present = set(df["occupation"].unique())
    missing = VALID_OCCUPATIONS - present
    assert missing == set(), f"不足職業: {missing}"


def test_application_id_unique(df):
    dupes = df["application_id"].duplicated().sum()
    assert dupes == 0, f"申込ID重複: {dupes}件"

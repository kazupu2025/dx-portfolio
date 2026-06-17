# -*- coding: utf-8 -*-
import os
import re
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "output", "cleaned_shift_202401.csv")

VALID_ROLES = {"レジ", "品出し", "フロア"}
EXPECTED_STORES = {"新宿店", "渋谷店", "池袋店", "銀座店", "品川店"}
EXPECTED_SOURCES = {"shift_styleA.csv", "shift_styleB.csv", "shift_styleC.csv"}

CANONICAL_COLS = [
    "shift_date", "store_id", "store_name", "role",
    "required_staff", "actual_staff", "work_hours", "hourly_rate",
    "daily_wage", "staffing_gap", "is_understaffed", "labor_cost_flag", "source_file"
]


@pytest.fixture(scope="module")
def df():
    assert os.path.exists(CSV_PATH), f"CSV not found: {CSV_PATH}"
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def test_file_exists():
    assert os.path.exists(CSV_PATH)


def test_row_count(df):
    assert len(df) >= 280


def test_canonical_columns(df):
    for col in CANONICAL_COLS:
        assert col in df.columns, f"Missing column: {col}"


def test_shift_date_format(df):
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    assert df["shift_date"].dropna().apply(lambda x: bool(pattern.match(str(x)))).all()


def test_store_names(df):
    assert set(df["store_name"].unique()) == EXPECTED_STORES


def test_roles(df):
    assert set(df["role"].unique()) == VALID_ROLES


def test_required_staff_positive(df):
    assert (df["required_staff"] >= 1).all()


def test_actual_staff_non_negative(df):
    assert (df["actual_staff"] >= 0).all()


def test_daily_wage_non_negative(df):
    assert (df["daily_wage"] >= 0).all()


def test_staffing_gap_calculation(df):
    expected = df["actual_staff"] - df["required_staff"]
    assert (df["staffing_gap"] == expected).all()


def test_is_understaffed_binary(df):
    assert set(df["is_understaffed"].unique()).issubset({0, 1})


def test_is_understaffed_consistency(df):
    expected = (df["staffing_gap"] < 0).astype(int)
    assert (df["is_understaffed"] == expected).all()


def test_labor_cost_flag_kinds(df):
    assert set(df["labor_cost_flag"].unique()) == {"高コスト", "通常"}


def test_source_file_three_kinds(df):
    assert set(df["source_file"].unique()) == EXPECTED_SOURCES


def test_missing_rate(df):
    total = df.shape[0] * df.shape[1]
    missing = df.isnull().sum().sum()
    assert missing / total <= 0.15

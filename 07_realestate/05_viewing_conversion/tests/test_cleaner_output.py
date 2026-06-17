# -*- coding: utf-8 -*-
import os
import pandas as pd
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "output", "cleaned_visits_202401.csv")

CANONICAL_COLS = [
    "visit_date", "visit_id", "property_type", "area", "staff_id",
    "asking_price", "visit_count_cumulative", "days_to_contract",
    "is_contracted", "price_tier", "conversion_speed", "source_file",
]


@pytest.fixture(scope="module")
def df():
    assert os.path.exists(CSV_PATH), "cleaned CSV not found"
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def test_file_exists():
    assert os.path.exists(CSV_PATH)


def test_row_count(df):
    assert len(df) >= 420


def test_canonical_columns_exist(df):
    for col in CANONICAL_COLS:
        assert col in df.columns, f"Missing column: {col}"


def test_visit_date_format(df):
    try:
        pd.to_datetime(df["visit_date"], format="%Y-%m-%d")
    except Exception as e:
        pytest.fail(f"visit_date format error: {e}")


def test_visit_id_unique(df):
    assert df["visit_id"].nunique() == len(df)


def test_property_type_four_kinds(df):
    assert df["property_type"].nunique() == 4


def test_area_four_kinds(df):
    assert df["area"].nunique() == 4


def test_asking_price_positive(df):
    prices = pd.to_numeric(df["asking_price"], errors="coerce")
    assert (prices > 0).all()


def test_is_contracted_binary(df):
    vals = pd.to_numeric(df["is_contracted"], errors="coerce").dropna().astype(int)
    assert set(vals.unique()).issubset({0, 1})


def test_price_tier_three_kinds(df):
    assert df["price_tier"].nunique() == 3


def test_conversion_speed_three_kinds(df):
    expected = {"早期成約", "通常成約", "未成約"}
    assert set(df["conversion_speed"].unique()) == expected


def test_days_to_contract_null_for_non_contracted(df):
    # Non-contracted rows should have null days_to_contract
    non_contracted = df[pd.to_numeric(df["is_contracted"], errors="coerce") == 0]
    null_count = non_contracted["days_to_contract"].isnull().sum()
    assert null_count == len(non_contracted), "Non-contracted rows should have null days_to_contract"


def test_source_file_three_kinds(df):
    assert df["source_file"].nunique() == 3


def test_missing_rate_excluding_days_to_contract(df):
    cols = [c for c in CANONICAL_COLS if c != "days_to_contract"]
    miss = df[cols].isnull().mean()
    assert (miss <= 0.15).all(), f"Missing rate too high: {miss[miss > 0.15]}"

"""
C-23: クレンジング出力の品質テスト
"""

from pathlib import Path

import pandas as pd
import pytest

BASE_DIR = Path(__file__).parent.parent
CSV_PATH = BASE_DIR / "output" / "cleaned_maintenance_202401.csv"

REQUIRED_COLS = [
    "property_id", "property_name", "area", "property_type",
    "cost_category", "occurrence_date", "cost_amount", "vendor_name",
    "is_urgent", "cost_per_unit_flag", "is_repair", "source_file",
]


@pytest.fixture(scope="module")
def df():
    assert CSV_PATH.exists(), f"CSV が存在しない: {CSV_PATH}"
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def test_csv_exists():
    assert CSV_PATH.exists(), f"CSV が存在しない: {CSV_PATH}"


def test_row_count(df):
    assert len(df) >= 400, f"行数不足: {len(df)}"


def test_required_columns(df):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    assert not missing, f"必須列が不足: {missing}"


def test_occurrence_date_format(df):
    invalid = df["occurrence_date"].dropna().apply(
        lambda v: not str(v).strip()[:10].replace("-", "").isdigit()
    )
    assert not invalid.any(), f"不正な occurrence_date が {invalid.sum()} 件"


def test_is_urgent_is_bool(df):
    unique_vals = set(df["is_urgent"].dropna().unique())
    assert unique_vals.issubset({True, False}), f"is_urgent に bool 以外の値: {unique_vals}"


def test_cost_amount_positive(df):
    assert (df["cost_amount"] > 0).all(), "cost_amount に 0 以下の値が存在する"


def test_cost_per_unit_flag_values(df):
    expected = {"高額", "中額", "少額"}
    actual = set(df["cost_per_unit_flag"].dropna().unique())
    assert actual.issubset(expected), f"cost_per_unit_flag に想定外の値: {actual - expected}"


def test_property_id_count(df):
    n = df["property_id"].nunique()
    assert n >= 30, f"property_id の種類数不足: {n}"


def test_area_count(df):
    areas = set(df["area"].dropna().unique())
    assert len(areas) == 5, f"area の種類数が5でない: {areas}"


def test_source_file_col(df):
    assert df["source_file"].notna().all(), "source_file に NULL がある"
    assert df["source_file"].nunique() == 3, f"source_file の種類数が3でない: {df['source_file'].nunique()}"

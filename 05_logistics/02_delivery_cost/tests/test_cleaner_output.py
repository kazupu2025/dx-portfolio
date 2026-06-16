"""
C-17 テスト: cleanse.py 出力チェック
"""
import re
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CSV_PATH = BASE_DIR / "output" / "cleaned_delivery_202401.csv"

REQUIRED_COLS = [
    "delivery_id", "date", "route_id", "vehicle_type", "distance_km",
    "fuel_cost", "toll_cost", "driver_cost", "total_cost", "status",
    "source_file", "cost_per_km", "cost_per_delivery",
]


@pytest.fixture(scope="module")
def df():
    assert CSV_PATH.exists(), f"CSV not found: {CSV_PATH}"
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def test_csv_exists():
    assert CSV_PATH.exists(), f"cleaned CSV not found: {CSV_PATH}"


def test_row_count(df):
    assert len(df) >= 400, f"Expected >= 400 rows, got {len(df)}"


def test_required_columns(df):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    assert not missing, f"Missing columns: {missing}"


def test_no_null_in_key_cols(df):
    key_cols = ["delivery_id", "date", "route_id", "vehicle_type", "status"]
    for col in key_cols:
        null_count = df[col].isnull().sum()
        assert null_count == 0, f"Column '{col}' has {null_count} nulls"


def test_date_format(df):
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    invalid = df["date"].dropna().apply(lambda x: not bool(pattern.match(str(x)))).sum()
    assert invalid == 0, f"{invalid} rows have invalid date format"


def test_numeric_cols_non_negative(df):
    for col in ["fuel_cost", "toll_cost", "driver_cost", "distance_km"]:
        neg = (pd.to_numeric(df[col], errors="coerce") < 0).sum()
        assert neg == 0, f"Column '{col}' has {neg} negative values"


def test_total_cost_integrity(df):
    calc = df["fuel_cost"] + df["toll_cost"] + df["driver_cost"]
    diff = (df["total_cost"] - calc).abs()
    mismatch = (diff > 1).sum()
    assert mismatch == 0, f"{mismatch} rows have total_cost mismatch"


def test_status_values(df):
    valid = {"完了", "遅延", "キャンセル"}
    invalid = (~df["status"].isin(valid)).sum()
    assert invalid == 0, f"{invalid} rows have invalid status values"


def test_vehicle_type_count(df):
    count = df["vehicle_type"].nunique()
    assert count == 4, f"Expected 4 vehicle types, got {count}"


def test_route_id_count(df):
    count = df["route_id"].nunique()
    assert count == 5, f"Expected 5 route IDs, got {count}"


def test_source_file_col(df):
    assert "source_file" in df.columns
    assert df["source_file"].notnull().all()


def test_null_rate(df):
    null_rate = df[["delivery_id", "date", "route_id", "status"]].isnull().mean().max()
    assert null_rate <= 0.15, f"Null rate too high: {null_rate:.1%}"


def test_cost_per_km_dtype(df):
    cpk = pd.to_numeric(df["cost_per_km"], errors="coerce")
    neg = (cpk < 0).sum()
    assert neg == 0, f"{neg} negative cost_per_km values"

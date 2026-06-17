# -*- coding: utf-8 -*-
import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "output", "cleaned_orders_202401.csv")

@pytest.fixture(scope="module")
def df():
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")

def test_file_exists():
    assert os.path.exists(CSV_PATH), "cleaned_orders_202401.csv does not exist"

def test_row_count(df):
    assert len(df) >= 420, f"Expected >= 420 rows, got {len(df)}"

def test_required_columns(df):
    required = [
        "order_date", "order_id", "shop_name", "work_type", "tech_id",
        "estimated_days", "actual_days", "labor_cost", "parts_cost", "status",
        "total_cost", "delay_days", "is_delayed", "is_returned",
        "efficiency_flag", "source_file",
    ]
    for col in required:
        assert col in df.columns, f"Missing column: {col}"

def test_order_date_format(df):
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    assert df["order_date"].dropna().str.match(pattern).all(), "order_date format is not YYYY-MM-DD"

def test_order_id_unique(df):
    assert df["order_id"].nunique() == len(df), "order_id has duplicates"

def test_shop_name_3_kinds(df):
    assert df["shop_name"].nunique() == 3, f"Expected 3 shops, got {df['shop_name'].nunique()}"

def test_work_type_4_kinds(df):
    assert df["work_type"].nunique() == 4, f"Expected 4 work types, got {df['work_type'].nunique()}"

def test_is_delayed_binary(df):
    assert set(df["is_delayed"].unique()).issubset({0, 1}), "is_delayed contains values other than 0/1"

def test_is_returned_binary(df):
    assert set(df["is_returned"].unique()).issubset({0, 1}), "is_returned contains values other than 0/1"

def test_efficiency_flag_2_kinds(df):
    assert df["efficiency_flag"].nunique() == 2, f"Expected 2 efficiency_flag values, got {df['efficiency_flag'].nunique()}"

def test_total_cost_equals_sum(df):
    calculated = df["labor_cost"] + df["parts_cost"]
    assert (abs(df["total_cost"] - calculated) < 1).all(), "total_cost != labor_cost + parts_cost"

def test_delay_days_equals_diff(df):
    calculated = df["actual_days"] - df["estimated_days"]
    assert (abs(df["delay_days"] - calculated) < 1).all(), "delay_days != actual_days - estimated_days"

def test_source_file_3_kinds(df):
    assert df["source_file"].nunique() == 3, f"Expected 3 source files, got {df['source_file'].nunique()}"

def test_returned_count(df):
    returned = (df["status"] == "再入庫").sum()
    assert returned >= 1, "No re-entry (再入庫) records found"

def test_no_null_order_id(df):
    assert df["order_id"].isnull().sum() == 0, "order_id has null values"

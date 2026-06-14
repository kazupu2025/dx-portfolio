import pandas as pd
import pytest
from pathlib import Path

CSV = Path("output/cleaned_inventory_202401.csv")


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(CSV, encoding="utf-8-sig")


def test_csv_exists():
    assert CSV.exists()

def test_row_count(df):
    assert 400 <= len(df) <= 1000

def test_required_columns(df):
    required = {"date", "warehouse", "item_code", "item_name", "category",
                "stock_qty", "min_stock_qty", "unit_cost",
                "received_qty", "shipped_qty", "source_file"}
    assert required.issubset(set(df.columns))

def test_warehouse_count(df):
    assert df["warehouse"].nunique() == 5

def test_no_null_date(df):
    assert df["date"].notna().all()

def test_no_null_warehouse(df):
    assert df["warehouse"].notna().all()

def test_stock_qty_nonneg(df):
    assert (df["stock_qty"] >= 0).all()

def test_min_stock_qty_nonneg(df):
    assert (df["min_stock_qty"] >= 0).all()

def test_unit_cost_nonneg(df):
    assert (df["unit_cost"] >= 0).all()

def test_received_qty_nonneg(df):
    assert (df["received_qty"] >= 0).all()

def test_shipped_qty_nonneg(df):
    assert (df["shipped_qty"] >= 0).all()

def test_expected_warehouses(df):
    assert "東京第1倉庫" in set(df["warehouse"].unique())

def test_col_order(df):
    assert list(df.columns[:3]) == ["date", "warehouse", "item_code"]

def test_source_file_nonempty(df):
    assert df["source_file"].notna().all()

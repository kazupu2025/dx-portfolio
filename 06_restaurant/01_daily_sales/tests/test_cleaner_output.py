import pandas as pd
import pytest
from pathlib import Path

CSV = Path("output/cleaned_sales_202401.csv")

@pytest.fixture(scope="module")
def df():
    return pd.read_csv(CSV, encoding="utf-8-sig")

def test_csv_exists():
    assert CSV.exists()

def test_row_count(df):
    assert 500 <= len(df) <= 1200

def test_required_columns(df):
    required = {"date", "store_name", "item_name", "category",
                "quantity", "unit_price", "sales_amount",
                "waste_qty", "waste_amount", "source_file"}
    assert required.issubset(set(df.columns))

def test_store_count(df):
    assert df["store_name"].nunique() == 5

def test_no_null_date(df):
    assert df["date"].notna().all()

def test_no_null_store(df):
    assert df["store_name"].notna().all()

def test_sales_amount_positive(df):
    assert (df["sales_amount"] > 0).all()

def test_waste_qty_nonneg(df):
    assert (df["waste_qty"] >= 0).all()

def test_waste_amount_nonneg(df):
    assert (df["waste_amount"] >= 0).all()

def test_quantity_positive(df):
    assert (df["quantity"] > 0).all()

def test_unit_price_positive(df):
    assert (df["unit_price"] > 0).all()

def test_expected_stores(df):
    stores = set(df["store_name"].unique())
    assert "渋谷店" in stores

def test_col_order(df):
    first_cols = list(df.columns[:3])
    assert first_cols == ["date", "store_name", "item_name"]

def test_source_file_nonempty(df):
    assert df["source_file"].notna().all()

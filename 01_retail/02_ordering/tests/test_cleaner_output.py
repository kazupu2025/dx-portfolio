import pandas as pd
import pytest
from pathlib import Path

CSV = Path("output/cleaned_order_2023Q4.csv")


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(CSV, encoding="utf-8-sig")


def test_csv_exists(): assert CSV.exists()

def test_row_count(df): assert 4000 <= len(df) <= 10000

def test_required_columns(df):
    required = {"date", "product_id", "product_name", "category",
                "sales_qty", "stock_qty", "reorder_point", "order_qty",
                "lead_time_days", "source_file"}
    assert required.issubset(set(df.columns))

def test_no_null_date(df): assert df["date"].notna().all()

def test_no_null_product_id(df): assert df["product_id"].notna().all()

def test_no_null_category(df): assert df["category"].notna().all()

def test_no_null_sales_qty(df): assert df["sales_qty"].notna().all()

def test_no_null_stock_qty(df): assert df["stock_qty"].notna().all()

def test_sales_qty_nonneg(df):
    assert (pd.to_numeric(df["sales_qty"], errors="coerce").fillna(0) >= 0).all()

def test_stock_qty_nonneg(df):
    assert (pd.to_numeric(df["stock_qty"], errors="coerce").fillna(0) >= 0).all()

def test_order_qty_nonneg(df):
    assert (pd.to_numeric(df["order_qty"], errors="coerce").fillna(0) >= 0).all()

def test_category_count(df): assert df["category"].nunique() == 5

def test_product_count(df): assert df["product_id"].nunique() == 50

def test_date_range(df):
    dates = pd.to_datetime(df["date"], errors="coerce")
    assert dates.dt.year.between(2023, 2023).all()
    assert dates.dt.month.between(10, 12).all()

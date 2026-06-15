import pandas as pd
import pytest
from pathlib import Path

CSV = Path("output/cleaned_cost_202401.csv")


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(CSV, encoding="utf-8-sig")


def test_csv_exists():
    assert CSV.exists()


def test_row_count(df):
    assert 400 <= len(df) <= 2000


def test_required_columns(df):
    required = {
        "date", "store", "ingredient_code", "ingredient_name", "category",
        "purchase_qty", "unit_cost", "used_qty", "waste_qty",
        "purchase_cost", "waste_cost", "waste_rate", "source_file",
    }
    assert required.issubset(set(df.columns))


def test_store_count(df):
    assert df["store"].nunique() == 5


def test_no_null_date(df):
    assert df["date"].notna().all()


def test_no_null_store(df):
    assert df["store"].notna().all()


def test_no_null_ingredient_code(df):
    assert df["ingredient_code"].notna().all()


def test_purchase_qty_nonneg(df):
    assert (df["purchase_qty"] >= 0).all()


def test_unit_cost_nonneg(df):
    assert (df["unit_cost"] >= 0).all()


def test_waste_qty_nonneg(df):
    assert (df["waste_qty"] >= 0).all()


def test_purchase_cost_nonneg(df):
    assert (df["purchase_cost"] >= 0).all()


def test_waste_cost_nonneg(df):
    assert (df["waste_cost"] >= 0).all()


def test_waste_rate_range(df):
    assert df["waste_rate"].between(0, 1).all()


def test_expected_store(df):
    assert "渋谷店" in set(df["store"].unique())

import pandas as pd
import pytest
from pathlib import Path

CSV = Path(__file__).parent.parent / "output" / "cleaned_rental_202401.csv"

@pytest.fixture(scope="module")
def df():
    return pd.read_csv(CSV, encoding="utf-8-sig")

def test_csv_exists(): assert CSV.exists()
def test_row_count(df): assert 100 <= len(df) <= 1000
def test_required_columns(df):
    required = {"property_id", "property_name", "area", "property_type",
                "rent", "management_fee", "occupancy_status",
                "is_vacant", "monthly_revenue", "total_cost", "net_income", "source_file"}
    assert required.issubset(set(df.columns))
def test_area_count(df): assert df["area"].nunique() == 5
def test_property_type_count(df): assert df["property_type"].nunique() == 5
def test_no_null_property_id(df): assert df["property_id"].notna().all()
def test_no_null_area(df): assert df["area"].notna().all()
def test_no_null_property_type(df): assert df["property_type"].notna().all()
def test_no_null_rent(df): assert df["rent"].notna().all()
def test_no_null_occupancy(df): assert df["occupancy_status"].notna().all()
def test_rent_nonneg(df): assert (pd.to_numeric(df["rent"], errors="coerce").fillna(0) >= 0).all()
def test_revenue_nonneg(df): assert (pd.to_numeric(df["monthly_revenue"], errors="coerce").fillna(0) >= 0).all()
def test_status_values(df):
    valid = {"入居中", "空室", "募集中"}
    assert set(df["occupancy_status"].unique()).issubset(valid)
def test_expected_area(df): assert "渋谷区" in set(df["area"].unique())

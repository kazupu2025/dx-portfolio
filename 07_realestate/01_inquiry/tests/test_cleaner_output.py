import pandas as pd
import pytest
from pathlib import Path

BASE = Path(__file__).parent.parent
CSV = BASE / "output" / "cleaned_inquiry_202401.csv"

@pytest.fixture(scope="module")
def df():
    return pd.read_csv(CSV, encoding="utf-8-sig")

def test_csv_exists(): assert CSV.exists()
def test_row_count(df): assert 300 <= len(df) <= 1500
def test_required_columns(df):
    required = {"date", "inquiry_id", "agent", "area", "property_type",
                "channel", "status", "is_contracted", "contract_amount", "source_file"}
    assert required.issubset(set(df.columns))
def test_area_count(df): assert df["area"].nunique() == 5
def test_no_null_date(df): assert df["date"].notna().all()
def test_no_null_area(df): assert df["area"].notna().all()
def test_no_null_status(df): assert df["status"].notna().all()
def test_no_null_agent(df): assert df["agent"].notna().all()
def test_status_valid(df):
    valid = {"問い合わせ", "内見", "申し込み", "成約"}
    assert set(df["status"].unique()).issubset(valid)
def test_is_contracted_binary(df):
    assert set(df["is_contracted"].unique()).issubset({0, 1})
def test_amount_nonneg(df): assert (df["contract_amount"] >= 0).all()
def test_flag_status_consistent(df):
    inconsistent = ((df["is_contracted"] == 1) & (df["status"] != "成約")).sum()
    assert inconsistent == 0
def test_expected_area(df): assert "渋谷区" in set(df["area"].unique())
def test_col_order(df): assert list(df.columns[:3]) == ["date", "inquiry_id", "agent"]

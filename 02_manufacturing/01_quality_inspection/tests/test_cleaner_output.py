import pandas as pd
import pytest
from pathlib import Path

CSV = Path("output/cleaned_inspection_202401.csv")

@pytest.fixture(scope="module")
def df():
    return pd.read_csv(CSV, encoding="utf-8-sig")

def test_csv_exists(): assert CSV.exists()
def test_row_count(df): assert 400 <= len(df) <= 1500
def test_required_columns(df):
    required = {"date", "product_code", "product_name", "process", "lot_no",
                "inspection_value", "lower_limit", "upper_limit",
                "result", "is_defect", "source_file"}
    assert required.issubset(set(df.columns))
def test_process_count(df): assert df["process"].nunique() == 5
def test_no_null_date(df): assert df["date"].notna().all()
def test_no_null_process(df): assert df["process"].notna().all()
def test_no_null_inspection_value(df): assert df["inspection_value"].notna().all()
def test_no_null_lower_limit(df): assert df["lower_limit"].notna().all()
def test_no_null_upper_limit(df): assert df["upper_limit"].notna().all()
def test_limits_valid(df): assert (df["lower_limit"] < df["upper_limit"]).all()
def test_result_values(df): assert set(df["result"].unique()).issubset({"OK", "NG"})
def test_defect_rate_reasonable(df):
    rate = df["is_defect"].mean()
    assert 0 < rate < 0.5
def test_expected_process(df): assert "切削工程" in set(df["process"].unique())
def test_col_order(df): assert list(df.columns[:3]) == ["date", "product_code", "product_name"]

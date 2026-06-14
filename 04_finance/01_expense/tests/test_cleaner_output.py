import pandas as pd
import pytest
from pathlib import Path

CSV = Path("output/cleaned_expense_202401.csv")

@pytest.fixture(scope="module")
def df():
    return pd.read_csv(CSV, encoding="utf-8-sig")

def test_csv_exists(): assert CSV.exists()
def test_row_count(df): assert 300 <= len(df) <= 800
def test_required_columns(df):
    required = {"date", "employee_id", "employee_name", "department",
                "expense_type", "amount", "budget", "receipt_no", "source_file"}
    assert required.issubset(set(df.columns))
def test_department_count(df): assert df["department"].nunique() == 5
def test_no_null_date(df): assert df["date"].notna().all()
def test_no_null_department(df): assert df["department"].notna().all()
def test_amount_nonneg(df): assert (df["amount"] >= 0).all()
def test_budget_nonneg(df): assert (df["budget"] >= 0).all()
def test_no_null_employee_id(df): assert df["employee_id"].notna().all()
def test_no_null_expense_type(df): assert df["expense_type"].notna().all()
def test_expected_departments(df): assert "営業部" in set(df["department"].unique())
def test_col_order(df): assert list(df.columns[:3]) == ["date", "employee_id", "employee_name"]
def test_source_file_nonempty(df): assert df["source_file"].notna().all()
def test_expense_type_valid(df):
    valid = {"交通費", "宿泊費", "接待費", "消耗品費", "通信費", "研修費"}
    assert set(df["expense_type"].unique()).issubset(valid)

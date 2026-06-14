import pandas as pd
import pytest
from pathlib import Path

CSV = Path("output/cleaned_attendance_202401.csv")


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(CSV, encoding="utf-8-sig")


def test_csv_exists():
    assert CSV.exists()


def test_row_count(df):
    assert 300 <= len(df) <= 1600


def test_required_columns(df):
    required = {"date", "employee_id", "employee_name", "department",
                "clock_in", "clock_out", "break_minutes", "paid_leave",
                "actual_work_hours", "overtime_hours", "source_file"}
    assert required.issubset(set(df.columns))


def test_department_count(df):
    assert df["department"].nunique() == 5


def test_no_null_date(df):
    assert df["date"].notna().all()


def test_no_null_department(df):
    assert df["department"].notna().all()


def test_no_null_clock_in(df):
    assert df["clock_in"].notna().all()


def test_no_null_clock_out(df):
    assert df["clock_out"].notna().all()


def test_work_hours_nonneg(df):
    assert (df["actual_work_hours"] >= 0).all()


def test_overtime_nonneg(df):
    assert (df["overtime_hours"] >= 0).all()


def test_work_hours_max(df):
    assert (df["actual_work_hours"] <= 20).all()


def test_expected_departments(df):
    assert "営業部" in set(df["department"].unique())


def test_col_order(df):
    assert list(df.columns[:3]) == ["date", "employee_id", "employee_name"]


def test_source_file_nonempty(df):
    assert df["source_file"].notna().all()

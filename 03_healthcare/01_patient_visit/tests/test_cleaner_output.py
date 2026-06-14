import pandas as pd
import pytest
from pathlib import Path

CSV = Path(__file__).parent.parent / "output" / "cleaned_visit_202401.csv"


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(CSV, encoding="utf-8-sig")


def test_csv_exists(): assert CSV.exists()
def test_row_count(df): assert 400 <= len(df) <= 3000
def test_required_columns(df):
    required = {"date", "weekday", "patient_id", "department",
                "reception_time", "hour_slot", "wait_minutes",
                "is_long_wait", "source_file"}
    assert required.issubset(set(df.columns))
def test_department_count(df): assert df["department"].nunique() == 5
def test_no_null_date(df): assert df["date"].notna().all()
def test_no_null_department(df): assert df["department"].notna().all()
def test_no_null_reception_time(df): assert df["reception_time"].notna().all()
def test_no_null_hour_slot(df): assert df["hour_slot"].notna().all()
def test_hour_range(df):
    hs = pd.to_numeric(df["hour_slot"], errors="coerce")
    assert hs.between(8, 18).all()
def test_wait_minutes_nonneg(df):
    wm = pd.to_numeric(df["wait_minutes"], errors="coerce")
    assert (wm >= 0).all()
def test_weekday_valid(df):
    assert set(df["weekday"].dropna().unique()).issubset({"月","火","水","木","金","土","日"})
def test_expected_department(df): assert "内科" in set(df["department"].unique())
def test_col_order(df): assert list(df.columns[:3]) == ["date", "weekday", "patient_id"]
def test_source_file_nonempty(df): assert df["source_file"].notna().all()

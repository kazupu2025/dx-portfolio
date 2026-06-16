"""
C-22 テスト: cleanse.py 出力チェック
"""
import re
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CSV_PATH = BASE_DIR / "output" / "cleaned_driver_202401.csv"

REQUIRED_COLS = [
    "driver_id", "name", "office", "work_date",
    "departure_time", "return_time",
    "break_hours", "distance_km", "operation_type",
    "confinement_hours", "work_hours",
    "confinement_over_flag", "work_over_flag", "violation_flag",
    "source_file",
]

VALID_OFFICES = {"東京営業所", "大阪営業所", "名古屋営業所"}
VALID_OPERATION_TYPES = {"長距離", "中距離", "市内配送"}
VALID_VIOLATION_FLAGS = {"違反", "正常"}


@pytest.fixture(scope="module")
def df():
    assert CSV_PATH.exists(), f"CSV not found: {CSV_PATH}"
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def test_csv_exists():
    assert CSV_PATH.exists(), f"cleaned CSV not found: {CSV_PATH}"


def test_row_count(df):
    assert len(df) >= 400, f"Expected >= 400 rows, got {len(df)}"


def test_required_columns(df):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    assert not missing, f"Missing columns: {missing}"


def test_date_format(df):
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    invalid = df["work_date"].dropna().apply(
        lambda x: not bool(pattern.match(str(x)))
    ).sum()
    assert invalid == 0, f"{invalid} rows have invalid work_date format"


def test_driver_id_count(df):
    count = df["driver_id"].nunique()
    assert count >= 20, f"Expected >= 20 driver IDs, got {count}"


def test_office_count(df):
    count = df["office"].nunique()
    assert count == 3, f"Expected 3 offices, got {count}"


def test_operation_type_count(df):
    count = df["operation_type"].nunique()
    assert count == 3, f"Expected 3 operation types, got {count}"


def test_distance_km_positive(df):
    neg = (pd.to_numeric(df["distance_km"], errors="coerce") <= 0).sum()
    assert neg == 0, f"{neg} rows have non-positive distance_km"


def test_break_hours_non_negative(df):
    neg = (pd.to_numeric(df["break_hours"], errors="coerce") < 0).sum()
    assert neg == 0, f"{neg} rows have negative break_hours"


def test_confinement_hours_positive(df):
    neg = (pd.to_numeric(df["confinement_hours"], errors="coerce") <= 0).sum()
    assert neg == 0, f"{neg} rows have non-positive confinement_hours"


def test_work_hours_positive(df):
    neg = (pd.to_numeric(df["work_hours"], errors="coerce") <= 0).sum()
    assert neg == 0, f"{neg} rows have non-positive work_hours"


def test_violation_flag_values(df):
    invalid = (~df["violation_flag"].isin(VALID_VIOLATION_FLAGS)).sum()
    assert invalid == 0, f"{invalid} rows have invalid violation_flag"


def test_source_file_col(df):
    assert "source_file" in df.columns
    assert df["source_file"].notnull().all()


def test_office_values(df):
    invalid = (~df["office"].isin(VALID_OFFICES)).sum()
    assert invalid == 0, f"{invalid} rows have invalid office values"


def test_operation_type_values(df):
    invalid = (~df["operation_type"].isin(VALID_OPERATION_TYPES)).sum()
    assert invalid == 0, f"{invalid} rows have invalid operation_type values"


def test_violation_flag_consistency(df):
    conf_flag = df["confinement_over_flag"].astype(bool)
    work_flag = df["work_over_flag"].astype(bool)
    expected = (conf_flag | work_flag).map({True: "違反", False: "正常"})
    mismatch = (df["violation_flag"] != expected).sum()
    assert mismatch == 0, f"{mismatch} rows have inconsistent violation_flag"


def test_null_rate(df):
    null_rate = df[["driver_id", "work_date", "office", "violation_flag"]].isnull().mean().max()
    assert null_rate <= 0.15, f"Null rate too high: {null_rate:.1%}"

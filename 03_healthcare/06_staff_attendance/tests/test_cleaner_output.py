# -*- coding: utf-8 -*-
import os
import re
import pytest
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CLEANED_FILE = os.path.join(OUTPUT_DIR, "cleaned_attendance_202401.csv")

REQUIRED_COLS = [
    "work_date", "record_id", "staff_type", "department", "staff_id",
    "scheduled_hours", "actual_hours", "is_absent", "absence_reason",
    "overtime_hours", "utilization_rate", "attendance_flag", "overtime_flag",
    "source_file"
]

OPTIONAL_COLS = {"absence_reason"}


@pytest.fixture(scope="module")
def df():
    assert os.path.exists(CLEANED_FILE), "cleaned_attendance_202401.csv not found. Run cleanse.py first."
    return pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")


def test_file_exists():
    assert os.path.exists(CLEANED_FILE), "cleaned_attendance_202401.csv must exist"


def test_row_count(df):
    assert len(df) >= 420, "Expected >= 420 rows, got {}".format(len(df))


def test_required_columns(df):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    assert missing == [], "Missing columns: {}".format(missing)


def test_work_date_format(df):
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    invalid = df["work_date"].dropna().apply(lambda x: not bool(date_pattern.match(str(x))))
    assert not invalid.any(), "Invalid work_date format found"


def test_record_id_unique(df):
    assert df["record_id"].nunique() == len(df), "record_id has duplicates"


def test_staff_type_four_kinds(df):
    kinds = df["staff_type"].nunique()
    assert kinds == 4, "Expected 4 staff types, got {}".format(kinds)


def test_department_five_kinds(df):
    kinds = df["department"].nunique()
    assert kinds == 5, "Expected 5 departments, got {}".format(kinds)


def test_is_absent_binary(df):
    assert df["is_absent"].isin([0, 1]).all(), "is_absent must be 0 or 1"


def test_utilization_rate_non_negative(df):
    assert (df["utilization_rate"] >= 0).all(), "utilization_rate must be >= 0"


def test_attendance_flag_values(df):
    valid = {"出勤", "欠勤"}
    actual = set(df["attendance_flag"].dropna().unique())
    assert actual == valid, "attendance_flag must be one of {}".format(valid)


def test_overtime_flag_values(df):
    valid = {"残業あり", "残業なし"}
    actual = set(df["overtime_flag"].dropna().unique())
    assert actual == valid, "overtime_flag must be one of {}".format(valid)


def test_source_file_three_kinds(df):
    kinds = df["source_file"].nunique()
    assert kinds == 3, "Expected 3 source files, got {}".format(kinds)


def test_absence_reason_null_for_present(df):
    present_rows = df[df["is_absent"] == 0]
    # absence_reason should be NaN for present staff
    assert present_rows["absence_reason"].isna().all(), \
        "absence_reason should be NaN for present staff (is_absent==0)"


def test_absence_reason_set_for_absent(df):
    absent_rows = df[df["is_absent"] == 1]
    # absence_reason should have at least some non-null values
    assert absent_rows["absence_reason"].notna().any(), \
        "absence_reason should have some values for absent staff"


def test_missing_rate_excluding_optional(df):
    check_cols = [c for c in REQUIRED_COLS if c not in OPTIONAL_COLS]
    max_null_rate = df[check_cols].isnull().mean().max()
    assert max_null_rate <= 0.15, "Missing rate > 15% in non-optional columns"


def test_overtime_hours_non_negative(df):
    assert (df["overtime_hours"] >= 0).all(), "overtime_hours must be >= 0"


def test_scheduled_hours_positive(df):
    assert (df["scheduled_hours"] > 0).all(), "scheduled_hours must be > 0"

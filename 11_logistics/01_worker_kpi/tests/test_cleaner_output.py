# -*- coding: utf-8 -*-
import os
import re
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "output", "cleaned_worker_kpi_202401.csv")

VALID_ZONES = {"入荷", "保管", "出荷", "検品"}
VALID_TASKS = {"フォークリフト", "ピッキング", "仕分け"}
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CANONICAL_COLS = [
    "work_date", "worker_id", "zone", "task_type",
    "processed_qty", "error_qty", "work_hours", "overtime_hours",
    "error_rate", "throughput", "kpi_flag", "source_file"
]


@pytest.fixture(scope="module")
def df():
    assert os.path.exists(CSV_PATH), f"CSV not found: {CSV_PATH}"
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def test_file_exists():
    assert os.path.exists(CSV_PATH)


def test_row_count(df):
    assert len(df) >= 380


def test_canonical_columns(df):
    for col in CANONICAL_COLS:
        assert col in df.columns, f"Missing column: {col}"


def test_work_date_format(df):
    invalid = df["work_date"].astype(str).apply(lambda x: not bool(DATE_PATTERN.match(x)))
    assert not invalid.any(), f"Invalid date formats: {df.loc[invalid, 'work_date'].tolist()[:5]}"


def test_valid_zones(df):
    actual = set(df["zone"].dropna().unique())
    assert actual == VALID_ZONES, f"Zone mismatch: {actual}"


def test_valid_tasks(df):
    actual = set(df["task_type"].dropna().unique())
    assert actual == VALID_TASKS, f"Task mismatch: {actual}"


def test_processed_qty_positive(df):
    assert (df["processed_qty"] >= 1).all()


def test_error_rate_range(df):
    valid = df["error_rate"].dropna()
    assert ((valid >= 0) & (valid <= 1)).all()


def test_throughput_positive(df):
    valid = df["throughput"].dropna()
    assert (valid > 0).all()


def test_kpi_flag_values(df):
    actual = set(df["kpi_flag"].dropna().unique())
    assert actual == {"優秀", "標準"}, f"Unexpected kpi_flag values: {actual}"


def test_source_file_count(df):
    assert df["source_file"].nunique() >= 3


def test_worker_count(df):
    assert df["worker_id"].nunique() >= 15


def test_overtime_hours_non_negative(df):
    assert (df["overtime_hours"] >= 0).all()

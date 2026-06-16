"""
C-20: クレンジング出力の品質テスト
"""

from pathlib import Path

import pandas as pd
import pytest

BASE_DIR = Path(__file__).parent.parent
CSV_PATH = BASE_DIR / "output" / "cleaned_labor_202401.csv"

REQUIRED_COLS = [
    "staff_id", "name", "store_id", "employment_type",
    "hourly_wage", "work_date", "clock_in", "clock_out",
    "break_minutes", "work_hours", "late_night",
    "base_wage", "late_night_premium", "total_wage", "overtime_hours",
    "source_file",
]


@pytest.fixture(scope="module")
def df():
    assert CSV_PATH.exists(), f"CSV が存在しない: {CSV_PATH}"
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def test_csv_exists():
    assert CSV_PATH.exists(), f"CSV が存在しない: {CSV_PATH}"


def test_row_count(df):
    assert len(df) >= 400, f"行数不足: {len(df)}"


def test_required_columns(df):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    assert not missing, f"必須列が不足: {missing}"


def test_work_date_format(df):
    invalid = df["work_date"].dropna().apply(
        lambda v: not str(v).strip()[:10].replace("-", "").isdigit()
    )
    assert not invalid.any(), f"不正な work_date が {invalid.sum()} 件"


def test_late_night_is_bool(df):
    unique_vals = set(df["late_night"].dropna().unique())
    assert unique_vals.issubset({True, False}), f"late_night に bool 以外の値: {unique_vals}"


def test_wage_calculation_consistency(df):
    """base_wage = hourly_wage * work_hours の整合性"""
    expected = (df["hourly_wage"] * df["work_hours"]).round(2)
    diff = (df["base_wage"] - expected).abs()
    assert (diff <= 1.0).all(), f"base_wage の計算不一致: 最大誤差 {diff.max():.2f}"


def test_total_wage_gte_base_wage(df):
    assert (df["total_wage"] >= df["base_wage"]).all(), "total_wage < base_wage の行が存在する"


def test_store_ids(df):
    expected = {"R001_新宿店", "R002_渋谷店", "R003_池袋店"}
    actual = set(df["store_id"].unique())
    assert actual == expected, f"店舗IDが一致しない: 期待={expected}, 実際={actual}"


def test_source_file_col(df):
    assert df["source_file"].notna().all(), "source_file に NULL がある"
    assert df["source_file"].nunique() == 3, f"source_file の種類数が3でない: {df['source_file'].nunique()}"

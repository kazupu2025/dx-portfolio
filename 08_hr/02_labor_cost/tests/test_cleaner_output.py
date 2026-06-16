"""
C-30: クレンジング出力の品質テスト (10テスト以上)
"""

import re
from pathlib import Path

import pandas as pd
import pytest

BASE_DIR = Path(__file__).parent.parent
CSV_PATH = BASE_DIR / "output" / "cleaned_labor_cost_202401.csv"

REQUIRED_COLS = [
    "year_month", "department", "employment_type",
    "head_count", "budget_cost", "actual_cost", "overtime_cost",
    "variance_amount", "variance_rate", "cost_per_person", "variance_flag",
    "source_file",
]

EXPECTED_DEPARTMENTS = {"営業部", "製造部", "管理部", "開発部", "物流部"}
EXPECTED_EMP_TYPES = {"正社員", "契約社員", "パート"}
EXPECTED_FLAGS = {"超過", "節約", "正常"}


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


def test_year_month_format(df):
    pattern = re.compile(r"^\d{4}-\d{2}$")
    invalid = df["year_month"].dropna().apply(
        lambda v: not bool(pattern.match(str(v).strip()))
    )
    assert not invalid.any(), f"不正な year_month が {invalid.sum()} 件"


def test_department_kinds(df):
    actual = set(df["department"].dropna().unique())
    assert actual == EXPECTED_DEPARTMENTS, f"部門が一致しない: 期待={EXPECTED_DEPARTMENTS}, 実際={actual}"


def test_employment_type_kinds(df):
    actual = set(df["employment_type"].dropna().unique())
    assert actual & EXPECTED_EMP_TYPES == EXPECTED_EMP_TYPES, \
        f"雇用区分に不足がある: 期待={EXPECTED_EMP_TYPES}, 実際={actual}"


def test_head_count_positive(df):
    invalid = (df["head_count"] <= 0).sum()
    assert invalid == 0, f"head_count <= 0 の行が {invalid} 件"


def test_budget_cost_positive(df):
    invalid = (df["budget_cost"] <= 0).sum()
    assert invalid == 0, f"budget_cost <= 0 の行が {invalid} 件"


def test_variance_flag_values(df):
    actual = set(df["variance_flag"].dropna().unique())
    assert actual.issubset(EXPECTED_FLAGS), f"variance_flag に想定外の値: {actual - EXPECTED_FLAGS}"


def test_source_file_col(df):
    assert "source_file" in df.columns, "source_file 列が存在しない"
    assert df["source_file"].notna().all(), "source_file に NULL がある"
    assert df["source_file"].nunique() == 3, \
        f"source_file の種類数が3でない: {df['source_file'].nunique()}"


def test_variance_amount_consistency(df):
    """variance_amount = actual_cost - budget_cost の整合性"""
    expected = df["actual_cost"] - df["budget_cost"]
    diff = (df["variance_amount"] - expected).abs()
    assert (diff <= 1.0).all(), f"variance_amount の計算不一致: 最大誤差 {diff.max():.2f}"


def test_overtime_cost_non_negative(df):
    invalid = (df["overtime_cost"] < 0).sum()
    assert invalid == 0, f"overtime_cost < 0 の行が {invalid} 件"

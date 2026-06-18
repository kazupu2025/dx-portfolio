# -*- coding: utf-8 -*-
"""
C-58: クレンジング出力の品質テスト (10テスト以上)
"""

from pathlib import Path

import pandas as pd
import pytest

BASE_DIR = Path(__file__).parent.parent
CSV_PATH = BASE_DIR / "output" / "cleaned_costs_202401.csv"

CANONICAL_COLS = [
    "record_date", "record_id", "project_no", "work_type", "cost_category",
    "budget_amount", "actual_amount", "is_over_budget",
    "variance", "variance_rate", "budget_status", "variance_grade", "source_file",
]


@pytest.fixture(scope="module")
def df():
    assert CSV_PATH.exists(), f"CSV が存在しない: {CSV_PATH}"
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def test_csv_exists():
    assert CSV_PATH.exists(), f"CSV が存在しない: {CSV_PATH}"


def test_row_count(df):
    assert len(df) >= 420, f"行数不足: {len(df)}"


def test_canonical_columns_present(df):
    missing = [c for c in CANONICAL_COLS if c not in df.columns]
    assert not missing, f"CANONICAL_COLS に不足列: {missing}"


def test_record_date_format(df):
    invalid = df["record_date"].dropna().apply(
        lambda v: not str(v).strip()[:10].replace("-", "").isdigit()
    )
    assert not invalid.any(), f"不正な record_date が {invalid.sum()} 件"


def test_record_id_unique(df):
    dup = df["record_id"].duplicated().sum()
    assert dup == 0, f"record_id に重複が {dup} 件"


def test_project_no_count(df):
    n = df["project_no"].nunique()
    assert n >= 4, f"project_no の種類数が 4 未満: {n}"


def test_work_type_four_kinds(df):
    expected = {"土工", "コンクリート工", "鉄筋工", "仮設工"}
    actual = set(df["work_type"].dropna().unique())
    assert expected.issubset(actual), f"work_type が足りない: 期待={expected}, 実際={actual}"


def test_cost_category_three_kinds(df):
    expected = {"材料費", "労務費", "外注費"}
    actual = set(df["cost_category"].dropna().unique())
    assert expected.issubset(actual), f"cost_category が足りない: 期待={expected}, 実際={actual}"


def test_budget_amount_positive(df):
    invalid = (df["budget_amount"] <= 0).sum()
    assert invalid == 0, f"budget_amount <= 0 の行: {invalid}"


def test_actual_amount_positive(df):
    invalid = (df["actual_amount"] <= 0).sum()
    assert invalid == 0, f"actual_amount <= 0 の行: {invalid}"


def test_is_over_budget_binary(df):
    unique_vals = set(df["is_over_budget"].dropna().unique())
    assert unique_vals.issubset({0, 1}), f"is_over_budget に 0/1 以外の値: {unique_vals}"


def test_variance_calculation(df):
    """variance = actual_amount - budget_amount"""
    expected = (df["actual_amount"] - df["budget_amount"]).round(0)
    diff = (df["variance"] - expected).abs()
    assert (diff <= 1.0).all(), f"variance の計算不一致: 最大誤差 {diff.max():.2f}"


def test_budget_status_two_kinds(df):
    expected = {"超過", "予算内"}
    actual = set(df["budget_status"].dropna().unique())
    assert expected.issubset(actual), f"budget_status が足りない: {actual}"


def test_variance_grade_three_kinds(df):
    expected = {"大超過", "小超過", "予算内"}
    actual = set(df["variance_grade"].dropna().unique())
    assert expected.issubset(actual), f"variance_grade が足りない: {actual}"


def test_source_file_three_kinds(df):
    n = df["source_file"].nunique()
    assert n == 3, f"source_file の種類数が 3 でない: {n}"


def test_no_all_nan_rows(df):
    all_nan = df[CANONICAL_COLS].isna().all(axis=1).sum()
    assert all_nan == 0, f"全列 NaN の行が {all_nan} 件"

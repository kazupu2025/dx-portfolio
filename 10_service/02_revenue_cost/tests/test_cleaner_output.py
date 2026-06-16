"""
C-21: クレンジング出力テスト
CSV存在・行数・列・利益計算整合性・profit_flag値
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).parent.parent
CSV_PATH = BASE / "output" / "cleaned_revenue_cost_202401.csv"

REQUIRED_COLS = [
    "project_id", "client_name", "service_type", "department",
    "contract_month", "revenue", "direct_cost", "allocated_overhead",
    "hours_spent", "is_completed", "source_file",
    "total_cost", "gross_profit", "operating_profit",
    "gross_margin_ratio", "operating_margin_ratio", "profit_flag",
]

VALID_PROFIT_FLAGS = {"赤字", "低収益", "良好"}


@pytest.fixture(scope="module")
def df():
    assert CSV_PATH.exists(), f"CSVが存在しません: {CSV_PATH}"
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def test_csv_exists():
    assert CSV_PATH.exists(), f"CSVが存在しません: {CSV_PATH}"


def test_row_count(df):
    assert len(df) >= 400, f"行数が400未満: {len(df)}"


def test_required_columns(df):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    assert len(missing) == 0, f"必須列が不足: {missing}"


def test_gross_profit_consistency(df):
    """gross_profit == revenue - direct_cost"""
    expected = (df["revenue"] - df["direct_cost"]).round(2)
    actual = df["gross_profit"].round(2)
    diff = (expected - actual).abs()
    assert (diff <= 1).all(), f"gross_profitの計算不整合: max_diff={diff.max()}"


def test_operating_profit_consistency(df):
    """operating_profit == revenue - total_cost"""
    expected = (df["revenue"] - df["total_cost"]).round(2)
    actual = df["operating_profit"].round(2)
    diff = (expected - actual).abs()
    assert (diff <= 1).all(), f"operating_profitの計算不整合: max_diff={diff.max()}"


def test_total_cost_consistency(df):
    """total_cost == direct_cost + allocated_overhead"""
    expected = (df["direct_cost"] + df["allocated_overhead"]).round(2)
    actual = df["total_cost"].round(2)
    diff = (expected - actual).abs()
    assert (diff <= 1).all(), f"total_costの計算不整合: max_diff={diff.max()}"


def test_profit_flag_values(df):
    invalid = ~df["profit_flag"].isin(VALID_PROFIT_FLAGS)
    assert not invalid.any(), f"無効なprofit_flag値: {df.loc[invalid, 'profit_flag'].unique()}"


def test_revenue_positive(df):
    invalid = (df["revenue"] <= 0).sum()
    assert invalid == 0, f"revenue <= 0 の行: {invalid}"


def test_source_file_present(df):
    nulls = df["source_file"].isna().sum()
    assert nulls == 0, f"source_fileが空の行: {nulls}"

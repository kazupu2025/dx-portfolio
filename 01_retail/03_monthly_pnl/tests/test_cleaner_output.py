"""
C-19: tests/test_cleaner_output.py
cleaned_pnl_202401.csv の品質テスト
"""
import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_FILE = os.path.join(BASE_DIR, "output", "cleaned_pnl_202401.csv")


@pytest.fixture(scope="module")
def df():
    assert os.path.isfile(CSV_FILE), f"File not found: {CSV_FILE}"
    return pd.read_csv(CSV_FILE, encoding="utf-8-sig")


def test_csv_exists():
    assert os.path.isfile(CSV_FILE)


def test_row_count(df):
    """行数が 400 以上あること（3スタイル × 65行 = 195行以上期待だが合算で400以上）"""
    assert len(df) >= 400, f"Expected >= 400 rows, got {len(df)}"


def test_required_columns(df):
    required = [
        "store_id", "store_name", "year_month",
        "planned_revenue", "actual_revenue",
        "planned_cogs", "actual_cogs",
        "planned_labor", "actual_labor",
        "planned_other", "actual_other",
        "actual_gross_profit", "actual_operating_profit",
        "revenue_variance", "profit_flag", "source_file",
    ]
    for col in required:
        assert col in df.columns, f"Missing column: {col}"


def test_actual_gross_profit_consistency(df):
    """actual_gross_profit = actual_revenue - actual_cogs"""
    diff = (df["actual_gross_profit"] - (df["actual_revenue"] - df["actual_cogs"])).abs()
    assert (diff <= 1).all(), f"Inconsistency found in actual_gross_profit: max diff={diff.max()}"


def test_actual_operating_profit_consistency(df):
    """actual_operating_profit = actual_gross_profit - actual_labor - actual_other"""
    diff = (
        df["actual_operating_profit"]
        - (df["actual_gross_profit"] - df["actual_labor"] - df["actual_other"])
    ).abs()
    assert (diff <= 1).all(), f"Inconsistency found in actual_operating_profit: max diff={diff.max()}"


def test_profit_flag_values(df):
    """profit_flag は 赤字/未達/達成 のみ"""
    valid = {"赤字", "未達", "達成"}
    bad = df[~df["profit_flag"].isin(valid)]
    assert len(bad) == 0, f"Invalid profit_flag values: {bad['profit_flag'].unique()}"


def test_store_id_variety(df):
    """5店舗以上あること"""
    assert df["store_id"].nunique() >= 5


def test_no_negative_revenue(df):
    """実績売上は正値"""
    assert (df["actual_revenue"] > 0).all()

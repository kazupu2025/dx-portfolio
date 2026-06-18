# -*- coding: utf-8 -*-
"""クレンジング出力テスト (10テスト以上)"""
import re
import pandas as pd
import pytest
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CSV_PATH = BASE_DIR / "output" / "cleaned_deliveries_202401.csv"

REQUIRED_COLS = [
    "delivery_date", "delivery_id", "delivery_type", "area", "vehicle_type",
    "delivery_charge", "fuel_cost", "driver_cost", "other_cost", "distance_km",
    "total_cost", "gross_profit", "profit_margin", "cost_per_km",
    "margin_grade", "source_file",
]


@pytest.fixture(scope="module")
def df():
    assert CSV_PATH.exists(), f"CSV not found: {CSV_PATH}"
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def test_csv_exists():
    assert CSV_PATH.exists()


def test_row_count(df):
    assert len(df) >= 420, f"行数不足: {len(df)}"


def test_required_columns(df):
    for col in REQUIRED_COLS:
        assert col in df.columns, f"列が存在しない: {col}"


def test_date_format(df):
    bad = df["delivery_date"].dropna().apply(
        lambda x: not bool(re.match(r"\d{4}-\d{2}-\d{2}", str(x)))
    )
    assert bad.sum() == 0, f"日付フォーマット不正: {bad.sum()}件"


def test_delivery_id_unique(df):
    assert df["delivery_id"].nunique() == len(df), \
        f"delivery_id 重複あり: {len(df) - df['delivery_id'].nunique()}件"


def test_delivery_type_variety(df):
    assert df["delivery_type"].nunique() == 4, \
        f"配送区分種類不正: {df['delivery_type'].nunique()}"


def test_area_variety(df):
    assert df["area"].nunique() == 5, \
        f"エリア種類不正: {df['area'].nunique()}"


def test_vehicle_type_variety(df):
    assert df["vehicle_type"].nunique() == 3, \
        f"車両タイプ種類不正: {df['vehicle_type'].nunique()}"


def test_delivery_charge_positive(df):
    assert (df["delivery_charge"] > 0).all(), "delivery_charge に0以下の値が存在する"


def test_fuel_cost_non_negative(df):
    assert (df["fuel_cost"] >= 0).all(), "fuel_cost に負の値が存在する"


def test_driver_cost_positive(df):
    assert (df["driver_cost"] > 0).all(), "driver_cost に0以下の値が存在する"


def test_distance_km_positive(df):
    assert (df["distance_km"] > 0).all(), "distance_km に0以下の値が存在する"


def test_gross_profit_consistency(df):
    computed = df["delivery_charge"] - (df["fuel_cost"] + df["driver_cost"] + df["other_cost"])
    diff = (df["gross_profit"] - computed).abs()
    assert (diff < 0.01).all(), f"gross_profit 不整合: {(diff >= 0.01).sum()}件"


def test_profit_margin_range(df):
    valid = df["profit_margin"].dropna()
    assert (valid <= 1).all(), "profit_margin が1を超えている（利益率100%超は不正）"


def test_margin_grade_values(df):
    valid_grades = {"高利益", "普通", "低利益"}
    actual = set(df["margin_grade"].dropna().unique())
    assert actual.issubset(valid_grades), f"無効なmargin_grade値: {actual - valid_grades}"


def test_source_file_variety(df):
    assert df["source_file"].nunique() == 3, \
        f"source_file の種類数不正: {df['source_file'].nunique()}"


def test_high_profit_exists(df):
    count = (df["margin_grade"] == "高利益").sum()
    assert count >= 1, f"高利益件数が0件"

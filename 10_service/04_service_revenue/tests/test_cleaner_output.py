# -*- coding: utf-8 -*-
"""
pytest: cleaned_revenue_202401.csv チェック (10テスト以上)
"""

import os
import numpy as np
import pandas as pd
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TARGET = os.path.join(OUTPUT_DIR, "cleaned_revenue_202401.csv")

REQUIRED_COLS = [
    "sale_date", "service_id", "service_name", "category", "client_id",
    "revenue", "cost", "gross_profit", "gross_margin", "profit_flag",
    "margin_grade", "source_file",
]
VALID_SERVICES = {"清掃", "警備", "設備管理", "受付代行", "IT保守", "コールセンター", "警備巡回", "施設管理"}
VALID_CATEGORIES = {"定期契約", "スポット", "複合"}
VALID_PROFIT_FLAGS = {"黒字", "赤字"}
VALID_MARGIN_GRADES = {"高利益", "中利益", "低利益"}
VALID_SOURCES = {
    "service_revenue_styleA.csv",
    "service_revenue_styleB.csv",
    "service_revenue_styleC.csv",
}
VALID_CLIENT_IDS = {"CLI-001", "CLI-002", "CLI-003", "CLI-004", "CLI-005"}
VALID_SERVICE_IDS = {f"SVC-00{i}" for i in range(1, 9)}


@pytest.fixture(scope="module")
def df():
    assert os.path.exists(TARGET), f"File not found: {TARGET}"
    return pd.read_csv(TARGET, encoding="utf-8-sig")


def test_file_exists():
    assert os.path.exists(TARGET)


def test_row_count(df):
    assert len(df) >= 420, f"Expected >= 420 rows, got {len(df)}"


def test_required_columns(df):
    missing = set(REQUIRED_COLS) - set(df.columns)
    assert missing == set(), f"Missing columns: {missing}"


def test_sale_date_format(df):
    parsed = pd.to_datetime(df["sale_date"], format="%Y-%m-%d", errors="coerce")
    assert parsed.notna().all(), "Some sale_date values could not be parsed as YYYY-MM-DD"


def test_service_name_8_types(df):
    vals = set(df["service_name"].dropna().unique())
    assert vals == VALID_SERVICES, f"Unexpected service names: {vals}"


def test_category_3_types(df):
    vals = set(df["category"].dropna().unique())
    assert vals == VALID_CATEGORIES, f"Unexpected categories: {vals}"


def test_revenue_positive(df):
    assert (df["revenue"] > 0).all(), "Some revenue values are not positive"


def test_cost_positive(df):
    assert (df["cost"] > 0).all(), "Some cost values are not positive"


def test_gross_profit_consistency(df):
    expected = (df["revenue"] - df["cost"]).round(2)
    actual = df["gross_profit"].round(2)
    assert (expected == actual).all(), "gross_profit != revenue - cost"


def test_gross_margin_range(df):
    gm = df["gross_margin"].dropna()
    assert ((gm >= -1) & (gm <= 1)).all(), "gross_margin out of [-1, 1]"


def test_profit_flag_values(df):
    vals = set(df["profit_flag"].dropna().unique())
    assert vals == VALID_PROFIT_FLAGS, f"Unexpected profit_flag values: {vals}"


def test_margin_grade_values(df):
    vals = set(df["margin_grade"].dropna().unique())
    assert vals == VALID_MARGIN_GRADES, f"Unexpected margin_grade values: {vals}"


def test_source_file_3_types(df):
    vals = set(df["source_file"].dropna().unique())
    assert vals == VALID_SOURCES, f"Unexpected source_file values: {vals}"


def test_client_id_5_types(df):
    vals = set(df["client_id"].dropna().unique())
    assert vals == VALID_CLIENT_IDS, f"Unexpected client_id values: {vals}"


def test_service_id_8_types(df):
    vals = set(df["service_id"].dropna().unique())
    assert vals == VALID_SERVICE_IDS, f"Unexpected service_id values: {vals}"


def test_deficit_records_exist(df):
    assert (df["profit_flag"] == "赤字").sum() >= 1, "No deficit records found"


def test_profit_records_exist(df):
    assert (df["profit_flag"] == "黒字").sum() >= 1, "No profit records found"


def test_missing_rate(df):
    missing_rate = df.isnull().mean().max()
    assert missing_rate <= 0.15, f"Missing rate too high: {missing_rate:.1%}"

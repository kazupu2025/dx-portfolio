# -*- coding: utf-8 -*-
"""
クレンジング出力ファイルのテスト (10テスト以上)
"""
import re
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CLEANED_CSV = BASE_DIR / "output" / "cleaned_route_202401.csv"


@pytest.fixture(scope="module")
def df():
    if not CLEANED_CSV.exists():
        pytest.skip("cleaned_route_202401.csv が存在しません。先にcleanse.pyを実行してください。")
    return pd.read_csv(CLEANED_CSV, encoding="utf-8-sig")


def test_csv_exists():
    """CSV ファイルが存在する"""
    assert CLEANED_CSV.exists(), f"ファイルが見つかりません: {CLEANED_CSV}"


def test_row_count(df):
    """行数が 400 以上である"""
    assert len(df) >= 400, f"行数が不足: {len(df)}"


def test_required_columns(df):
    """必須列がすべて存在する"""
    required = [
        "date", "route_id", "area", "vehicle_type",
        "distance_km", "duration_min", "fuel_cost",
        "delivery_count", "delay_flag",
        "cost_per_km", "cost_per_delivery", "km_per_delivery", "efficiency_flag"
    ]
    missing = [c for c in required if c not in df.columns]
    assert missing == [], f"不足列: {missing}"


def test_date_format(df):
    """日付列が YYYY-MM-DD 形式である"""
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    bad = df["date"].dropna().apply(lambda x: not pattern.match(str(x))).sum()
    assert bad == 0, f"不正な日付フォーマット: {bad}件"


def test_route_id_variety(df):
    """route_id が 10 種類である"""
    count = df["route_id"].nunique()
    assert count == 10, f"route_id の種類数: {count}"


def test_area_variety(df):
    """area が 5 種類である"""
    count = df["area"].nunique()
    assert count == 5, f"area の種類数: {count}"


def test_vehicle_type_variety(df):
    """vehicle_type が 3 種類である"""
    count = df["vehicle_type"].nunique()
    assert count == 3, f"vehicle_type の種類数: {count}"


def test_delay_flag_values(df):
    """delay_flag が 0 または 1 のみである"""
    bad = (~df["delay_flag"].isin([0, 1])).sum()
    assert bad == 0, f"不正な delay_flag 値: {bad}件"


def test_efficiency_flag_values(df):
    """efficiency_flag が '高効率' または '低効率' のみである"""
    bad = (~df["efficiency_flag"].isin(["高効率", "低効率"])).sum()
    assert bad == 0, f"不正な efficiency_flag 値: {bad}件"


def test_source_file_column(df):
    """source_file 列が存在する"""
    assert "source_file" in df.columns, "source_file 列が存在しません"


def test_distance_km_positive(df):
    """distance_km がすべて正の値である"""
    bad = (pd.to_numeric(df["distance_km"], errors="coerce") <= 0).sum()
    assert bad == 0, f"distance_km <= 0 の件数: {bad}"


def test_fuel_cost_positive(df):
    """fuel_cost がすべて正の値である"""
    bad = (pd.to_numeric(df["fuel_cost"], errors="coerce") <= 0).sum()
    assert bad == 0, f"fuel_cost <= 0 の件数: {bad}"

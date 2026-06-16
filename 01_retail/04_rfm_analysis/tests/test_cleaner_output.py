# -*- coding: utf-8 -*-
"""
test_cleaner_output.py
cleaned_purchases_202401.csv に対するバリデーションテスト（10テスト以上）
"""

import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
OUTPUT_FILE = BASE_DIR / "output" / "cleaned_purchases_202401.csv"

VALID_STORES = {"渋谷店", "新宿店", "池袋店"}
VALID_CATEGORIES = {"食料品", "日用品", "衣料品", "家電", "雑貨"}


@pytest.fixture(scope="module")
def df():
    if not OUTPUT_FILE.exists():
        pytest.skip(f"cleaned CSV が存在しません: {OUTPUT_FILE}")
    return pd.read_csv(OUTPUT_FILE, encoding="utf-8-sig")


# 1. CSVファイル存在確認
def test_csv_exists():
    assert OUTPUT_FILE.exists(), f"cleaned CSV が存在しません: {OUTPUT_FILE}"


# 2. 行数 >= 400
def test_row_count(df):
    assert len(df) >= 400, f"行数が不足しています: {len(df)} < 400"


# 3. 必須列の存在（5列）
def test_required_columns(df):
    required = ["order_date", "customer_code", "category", "amount", "store_name"]
    missing = [c for c in required if c not in df.columns]
    assert not missing, f"必須列が不足しています: {missing}"


# 4. 日付フォーマット YYYY-MM-DD
def test_date_format(df):
    bad = df[~df["order_date"].str.match(r"^\d{4}-\d{2}-\d{2}$")]
    assert len(bad) == 0, f"日付フォーマットが不正な行があります: {bad['order_date'].head().tolist()}"


# 5. customer_codeが50種類以上
def test_customer_code_variety(df):
    n = df["customer_code"].nunique()
    assert n >= 50, f"customer_code の種類数が不足しています: {n} < 50"


# 6. categoryが5種類
def test_category_count(df):
    n = df["category"].nunique()
    assert n == 5, f"category の種類数が期待値と異なります: {n} != 5"


# 7. store_nameが3種類
def test_store_name_count(df):
    n = df["store_name"].nunique()
    assert n == 3, f"store_name の種類数が期待値と異なります: {n} != 3"


# 8. amount > 0（全行）
def test_amount_positive(df):
    bad = df[df["amount"] <= 0]
    assert len(bad) == 0, f"amount <= 0 の行があります: {len(bad)}件"


# 9. source_file列の存在
def test_source_file_column(df):
    assert "source_file" in df.columns, "source_file 列が存在しません"


# 10. 2024年のデータのみ
def test_only_2024_dates(df):
    years = df["order_date"].str[:4].unique().tolist()
    non_2024 = [y for y in years if y != "2024"]
    assert not non_2024, f"2024年以外の年が含まれています: {non_2024}"


# 11. customer_codeが CUST- で始まる
def test_customer_code_format(df):
    bad = df[~df["customer_code"].str.startswith("CUST-")]
    assert len(bad) == 0, f"CUST- で始まらない customer_code があります: {bad['customer_code'].head().tolist()}"


# 12. store_nameが有効値のみ
def test_store_name_valid_values(df):
    invalid = set(df["store_name"].unique()) - VALID_STORES
    assert not invalid, f"無効な store_name が含まれています: {invalid}"


# 13. categoryが有効値のみ
def test_category_valid_values(df):
    invalid = set(df["category"].unique()) - VALID_CATEGORIES
    assert not invalid, f"無効な category が含まれています: {invalid}"


# 14. source_fileが3種類（3スタイル分）
def test_source_file_variety(df):
    if "source_file" not in df.columns:
        pytest.skip("source_file 列なし")
    n = df["source_file"].nunique()
    assert n == 3, f"source_file の種類数が期待値と異なります: {n} != 3"


# 15. amount の最大値 <= 100000（異常値チェック）
def test_amount_max(df):
    max_val = df["amount"].max()
    assert max_val <= 100000, f"amount の最大値が異常です: {max_val} > 100000"

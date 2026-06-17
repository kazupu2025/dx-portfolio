# -*- coding: utf-8 -*-
"""
test_cleaner_output.py

cleaned_claims_202401.csv の品質を検証するテスト群。
pytest で実行: pytest tests/test_cleaner_output.py -v
"""

import re
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CSV_PATH = BASE_DIR / "output" / "cleaned_claims_202401.csv"

EXPECTED_STORES = {"渋谷店", "新宿店", "池袋店", "銀座店", "上野店"}
EXPECTED_CATEGORIES = {"食料品", "日用品", "衣料品", "家電", "雑貨"}
EXPECTED_CLAIM_TYPES = {"品質不良", "サイズ不一致", "破損", "その他"}
EXPECTED_RESPONSE_LEVELS = {"迅速", "標準", "遅延"}
REQUIRED_COLUMNS = [
    "receipt_date", "case_no", "store_name", "category",
    "claim_type", "return_amount", "response_days", "resolved_flag",
    "is_resolved", "response_level", "source_file",
]
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@pytest.fixture(scope="module")
def df() -> pd.DataFrame:
    if not CSV_PATH.exists():
        pytest.skip(f"CSVが存在しません: {CSV_PATH}")
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


# ---- 基本構造テスト -------------------------------------------------------

def test_file_exists():
    """CSVファイルが存在する。"""
    assert CSV_PATH.exists(), f"ファイルが見つかりません: {CSV_PATH}"


def test_row_count(df):
    """行数が 400 以上である。"""
    assert len(df) >= 400, f"行数が不足: {len(df)}"


def test_required_columns_exist(df):
    """全必須列が存在する。"""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    assert not missing, f"不足列: {missing}"


def test_no_duplicate_case_no(df):
    """case_no に重複がない。"""
    duplicated = df["case_no"].duplicated().sum()
    assert duplicated == 0, f"重複 case_no: {duplicated} 件"


# ---- 日付テスト ----------------------------------------------------------

def test_date_format(df):
    """receipt_date が YYYY-MM-DD フォーマットである。"""
    bad = df["receipt_date"].astype(str).apply(lambda d: not bool(DATE_PATTERN.match(d))).sum()
    assert bad == 0, f"不正な日付形式: {bad} 件"


# ---- マスタ値テスト -------------------------------------------------------

def test_store_names(df):
    """store_name が期待する 5 種類のみ。"""
    actual = set(df["store_name"].unique())
    assert actual == EXPECTED_STORES, f"期待: {EXPECTED_STORES}, 実際: {actual}"


def test_categories(df):
    """category が期待する 5 種類のみ。"""
    actual = set(df["category"].unique())
    assert actual == EXPECTED_CATEGORIES, f"期待: {EXPECTED_CATEGORIES}, 実際: {actual}"


def test_claim_types(df):
    """claim_type が期待する 4 種類のみ。"""
    actual = set(df["claim_type"].unique())
    assert actual == EXPECTED_CLAIM_TYPES, f"期待: {EXPECTED_CLAIM_TYPES}, 実際: {actual}"


# ---- 数値テスト ----------------------------------------------------------

def test_return_amount_non_negative(df):
    """return_amount が全て 0 以上。"""
    neg = (df["return_amount"] < 0).sum()
    assert neg == 0, f"負の return_amount: {neg} 件"


def test_response_days_positive(df):
    """response_days が全て 1 以上。"""
    invalid = (df["response_days"] <= 0).sum()
    assert invalid == 0, f"response_days が 0 以下: {invalid} 件"


# ---- 計算列テスト --------------------------------------------------------

def test_is_resolved_binary(df):
    """is_resolved が 0 または 1 のみ。"""
    invalid = (~df["is_resolved"].isin([0, 1])).sum()
    assert invalid == 0, f"is_resolved に 0/1 以外の値: {invalid} 件"


def test_response_level_values(df):
    """response_level が 迅速/標準/遅延 のみ。"""
    invalid = (~df["response_level"].isin(EXPECTED_RESPONSE_LEVELS)).sum()
    assert invalid == 0, f"不正な response_level: {invalid} 件"


def test_response_level_logic(df):
    """response_level が response_days に基づいて正しく分類されている。"""
    def expected_level(days: int) -> str:
        if days <= 3:
            return "迅速"
        elif days <= 10:
            return "標準"
        else:
            return "遅延"

    mismatch = (
        df.apply(lambda row: row["response_level"] != expected_level(row["response_days"]), axis=1)
    ).sum()
    assert mismatch == 0, f"response_level の分類ミス: {mismatch} 件"


# ---- ソースファイルテスト ------------------------------------------------

def test_source_file_column_exists(df):
    """source_file 列が存在する。"""
    assert "source_file" in df.columns


def test_source_file_count(df):
    """source_file が 3 種類（3スタイルのCSV）。"""
    count = df["source_file"].nunique()
    assert count == 3, f"source_file の種類: {count}"


# ---- 解決率テスト --------------------------------------------------------

def test_unresolved_exists(df):
    """未解決件数が 1 以上存在する。"""
    unresolved = (df["is_resolved"] == 0).sum()
    assert unresolved >= 1, "未解決案件が存在しない"


def test_resolve_rate_gte_70pct(df):
    """解決率が 70% 以上。"""
    rate = df["is_resolved"].mean() * 100
    assert rate >= 70, f"解決率が低すぎます: {rate:.1f}%"

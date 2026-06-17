# -*- coding: utf-8 -*-
"""
C-54: 分析出力テスト（7テスト以上）
"""

import pytest
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output"
REPORT_FILE = OUTPUT_DIR / "analysis_report.md"
SUMMARY_FILE = OUTPUT_DIR / "store_pl_summary_202401.csv"

STORES_EXPECTED = {"渋谷店", "新宿店", "池袋店", "銀座店", "品川店"}


@pytest.fixture(scope="module")
def df_summary():
    assert SUMMARY_FILE.exists(), f"サマリーファイルが存在しません: {SUMMARY_FILE}"
    return pd.read_csv(SUMMARY_FILE, encoding="utf-8-sig")


@pytest.fixture(scope="module")
def report_text():
    assert REPORT_FILE.exists(), f"レポートファイルが存在しません: {REPORT_FILE}"
    return REPORT_FILE.read_text(encoding="utf-8")


# 1. analysis_report.md が存在すること
def test_report_file_exists():
    assert REPORT_FILE.exists(), f"レポートが見つかりません: {REPORT_FILE}"


# 2. store_pl_summary_202401.csv が存在すること
def test_summary_file_exists():
    assert SUMMARY_FILE.exists(), f"サマリーが見つかりません: {SUMMARY_FILE}"


# 3. サマリーCSV が 5 行（5店舗）
def test_summary_row_count(df_summary):
    assert len(df_summary) == 5, f"サマリー行数が不正: {len(df_summary)}"


# 4. サマリーCSV に必須列が含まれる
def test_summary_required_columns(df_summary):
    required = ["store_name", "total_revenue", "total_gross_profit", "pl_status"]
    for col in required:
        assert col in df_summary.columns, f"列が存在しない: {col}"


# 5. total_revenue が全て正の値
def test_summary_revenue_positive(df_summary):
    vals = pd.to_numeric(df_summary["total_revenue"], errors="coerce")
    assert (vals > 0).all(), "total_revenue に 0 以下の値が存在"


# 6. pl_status が 黒字/赤字 のみ
def test_summary_pl_status_values(df_summary):
    unique_vals = set(df_summary["pl_status"].unique())
    assert unique_vals.issubset({"黒字", "赤字"}), f"pl_status に不正な値: {unique_vals}"


# 7. レポートに5店舗が含まれる
def test_report_contains_stores(report_text):
    for store in STORES_EXPECTED:
        assert store in report_text, f"レポートに店舗が含まれない: {store}"


# 8. レポートに損益フラグが含まれる
def test_report_contains_pl_flag(report_text):
    assert "黒字" in report_text or "赤字" in report_text, "レポートに損益フラグが含まれない"


# 9. レポートに売上トレンドが含まれる
def test_report_contains_trend(report_text):
    assert "日別売上トレンド" in report_text, "レポートに日別売上トレンドが含まれない"


# 10. サマリーCSV の store_name が5種類
def test_summary_store_names(df_summary):
    stores = set(df_summary["store_name"].unique())
    assert stores == STORES_EXPECTED, f"store_name が期待値と異なる: {stores}"

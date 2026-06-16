# -*- coding: utf-8 -*-
"""
C-29: 薬品在庫管理・発注アラートパイプライン
分析出力テスト (7 テスト以上)
"""

import re
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
SUMMARY_CSV_PATH = OUTPUT_DIR / "medicine_summary_202401.csv"


# 1. analysis_report.md が存在する
def test_report_exists():
    assert REPORT_PATH.exists(), f"analysis_report.md が存在しません: {REPORT_PATH}"


# 2. medicine_summary_202401.csv が存在する
def test_summary_csv_exists():
    assert SUMMARY_CSV_PATH.exists(), f"medicine_summary_202401.csv が存在しません: {SUMMARY_CSV_PATH}"


@pytest.fixture(scope="module")
def report_text():
    assert REPORT_PATH.exists(), "analysis_report.md がない"
    return REPORT_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def df_summary():
    assert SUMMARY_CSV_PATH.exists(), "medicine_summary_202401.csv がない"
    return pd.read_csv(SUMMARY_CSV_PATH, encoding="utf-8-sig")


# 3. レポートに「薬品」が含まれる
def test_report_contains_medicine(report_text):
    assert "薬品" in report_text, "レポートに「薬品」が含まれません"


# 4. レポートに「欠品」が含まれる
def test_report_contains_shortage(report_text):
    assert "欠品" in report_text, "レポートに「欠品」が含まれません"


# 5. レポートにインサイトまたはまとめがある
def test_report_has_insight(report_text):
    has = "インサイト" in report_text or "まとめ" in report_text
    assert has, "レポートにインサイトまたはまとめがありません"


# 6. レポートに数値がある
def test_report_has_numbers(report_text):
    has = bool(re.search(r"\d+", report_text))
    assert has, "レポートに数値がありません"


# 7. medicine_summary_202401.csv の行数 >= 1
def test_summary_csv_rows(df_summary):
    assert len(df_summary) >= 1, f"medicine_summary_202401.csv の行数が {len(df_summary)} 件"


# 8. レポートに病棟別分析がある
def test_report_has_ward_analysis(report_text):
    assert "病棟" in report_text, "レポートに病棟別分析がありません"


# 9. レポートにカテゴリ別分析がある
def test_report_has_category_analysis(report_text):
    assert "カテゴリ" in report_text, "レポートにカテゴリ別分析がありません"

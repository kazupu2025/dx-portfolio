# -*- coding: utf-8 -*-
"""
C-37: 来客記録データ集計・スループット分析パイプライン
分析出力テスト (7 テスト以上)
"""

import re
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
SUMMARY_CSV_PATH = OUTPUT_DIR / "dept_summary_202401.csv"


# 1. analysis_report.md が存在する
def test_report_exists():
    assert REPORT_PATH.exists(), f"analysis_report.md が存在しません: {REPORT_PATH}"


# 2. dept_summary_202401.csv が存在する
def test_summary_csv_exists():
    assert SUMMARY_CSV_PATH.exists(), f"dept_summary_202401.csv が存在しません: {SUMMARY_CSV_PATH}"


@pytest.fixture(scope="module")
def report_text():
    assert REPORT_PATH.exists(), "analysis_report.md がない"
    return REPORT_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def df_summary():
    assert SUMMARY_CSV_PATH.exists(), "dept_summary_202401.csv がない"
    return pd.read_csv(SUMMARY_CSV_PATH, encoding="utf-8-sig")


# 3. レポートに「来院」が含まれる
def test_report_contains_visit(report_text):
    assert "来院" in report_text, "レポートに「来院」が含まれません"


# 4. レポートに「待ち時間」または「長待ち」が含まれる
def test_report_contains_wait(report_text):
    has = "待ち時間" in report_text or "長待ち" in report_text
    assert has, "レポートに「待ち時間」も「長待ち」も含まれません"


# 5. レポートにインサイトまたはまとめがある
def test_report_has_insight(report_text):
    has = "インサイト" in report_text or "まとめ" in report_text
    assert has, "レポートにインサイトまたはまとめがありません"


# 6. レポートに数値がある
def test_report_has_numbers(report_text):
    has = bool(re.search(r"\d+", report_text))
    assert has, "レポートに数値がありません"


# 7. dept_summary_202401.csv の行数 >= 1
def test_summary_csv_rows(df_summary):
    assert len(df_summary) >= 1, f"dept_summary_202401.csv の行数が {len(df_summary)} 件"


# 8. レポートに診療科別分析がある
def test_report_has_dept_analysis(report_text):
    assert "診療科" in report_text, "レポートに診療科別分析がありません"


# 9. レポートに時間帯分析がある
def test_report_has_timeslot_analysis(report_text):
    has = "時間帯" in report_text or "ピーク" in report_text
    assert has, "レポートに時間帯またはピーク分析がありません"


# 10. dept_summary の診療科が 5 種類
def test_summary_dept_count(df_summary):
    assert "department" in df_summary.columns, "dept_summary に department 列がない"
    n = df_summary["department"].nunique()
    assert n == 5, f"dept_summary の診療科が {n} 種類 (期待: 5)"

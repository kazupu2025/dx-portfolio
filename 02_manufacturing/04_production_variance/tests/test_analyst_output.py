# -*- coding: utf-8 -*-
"""
C-25: 分析出力テスト（7テスト以上）
"""
import re
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_MD = OUTPUT_DIR / "analysis_report.md"
LINE_SUMMARY_CSV = OUTPUT_DIR / "line_summary_202401.csv"

NUMBER_PATTERN = re.compile(r"\d{3,}")


# 1. analysis_report.md 存在確認
def test_report_exists():
    assert REPORT_MD.exists(), f"レポートが存在しません: {REPORT_MD}"


# 2. line_summary_202401.csv 存在確認
def test_line_summary_csv_exists():
    assert LINE_SUMMARY_CSV.exists(), f"CSVが存在しません: {LINE_SUMMARY_CSV}"


@pytest.fixture(scope="module")
def report_text():
    if not REPORT_MD.exists():
        pytest.skip(f"レポートが存在しません: {REPORT_MD}")
    return REPORT_MD.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def line_summary_df():
    if not LINE_SUMMARY_CSV.exists():
        pytest.skip(f"CSVが存在しません: {LINE_SUMMARY_CSV}")
    return pd.read_csv(LINE_SUMMARY_CSV, encoding="utf-8-sig")


# 3. レポートに「計画」含む
def test_report_contains_keikaku(report_text):
    assert "計画" in report_text, "レポートに「計画」が含まれていません"


# 4. レポートに「達成」含む
def test_report_contains_tassei(report_text):
    assert "達成" in report_text or "実績" in report_text, \
        "レポートに「達成」または「実績」が含まれていません"


# 5. レポートにインサイト・まとめがある
def test_report_has_insight(report_text):
    has_insight = "インサイト" in report_text or "まとめ" in report_text or "改善示唆" in report_text
    assert has_insight, "レポートにインサイト・まとめセクションが見つかりません"


# 6. レポートに数値（3桁以上）がある
def test_report_has_numbers(report_text):
    assert bool(NUMBER_PATTERN.search(report_text)), "レポートに3桁以上の数値が見つかりません"


# 7. line_summary CSVの行数 >= 1
def test_line_summary_row_count(line_summary_df):
    assert len(line_summary_df) >= 1, f"CSVが空です: {len(line_summary_df)} 行"


# 8. レポートにライン別分析がある
def test_report_has_line_analysis(report_text):
    has_line = "ライン別" in report_text or "LINE-" in report_text
    assert has_line, "レポートにライン別分析が見つかりません"


# 9. レポートに不良率分析がある
def test_report_has_defect_analysis(report_text):
    assert "不良率" in report_text or "不良" in report_text, \
        "レポートに不良率分析が見つかりません"

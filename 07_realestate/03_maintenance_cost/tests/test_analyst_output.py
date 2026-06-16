"""
C-23: 分析出力の品質テスト
"""

import re
from pathlib import Path

import pandas as pd
import pytest

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
SUMMARY_PATH = OUTPUT_DIR / "property_summary_202401.csv"


def test_report_exists():
    assert REPORT_PATH.exists(), f"analysis_report.md が存在しない: {REPORT_PATH}"


def test_summary_csv_exists():
    assert SUMMARY_PATH.exists(), f"property_summary_202401.csv が存在しない: {SUMMARY_PATH}"


@pytest.fixture(scope="module")
def report_text():
    assert REPORT_PATH.exists(), f"レポートが存在しない: {REPORT_PATH}"
    return REPORT_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def summary_df():
    assert SUMMARY_PATH.exists(), f"CSV が存在しない: {SUMMARY_PATH}"
    return pd.read_csv(SUMMARY_PATH, encoding="utf-8-sig")


def test_report_contains_shuzen(report_text):
    assert "修繕" in report_text, "レポートに「修繕」が含まれない"


def test_report_contains_cost(report_text):
    assert "コスト" in report_text or "費用" in report_text, "レポートに「コスト」または「費用」が含まれない"


def test_report_contains_insight(report_text):
    has_insight = "インサイト" in report_text or "まとめ" in report_text or "推奨" in report_text
    assert has_insight, "レポートにインサイト・まとめ・推奨が含まれない"


def test_report_contains_numbers(report_text):
    assert bool(re.search(r"\d{3,}", report_text)), "レポートに数値（3桁以上）が含まれない"


def test_summary_csv_row_count(summary_df):
    assert len(summary_df) >= 1, f"サマリーCSVの行数が不足: {len(summary_df)}"


def test_summary_csv_has_property_id(summary_df):
    assert "property_id" in summary_df.columns, "property_id 列が存在しない"


def test_summary_csv_has_total_cost(summary_df):
    assert "total_cost" in summary_df.columns, "total_cost 列が存在しない"

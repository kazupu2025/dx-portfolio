"""
C-30: 分析出力の品質テスト (7テスト以上)
"""

import re
from pathlib import Path

import pandas as pd
import pytest

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
CSV_PATH = OUTPUT_DIR / "dept_summary_202401.csv"


@pytest.fixture(scope="module")
def report_text():
    assert REPORT_PATH.exists(), f"レポートが存在しない: {REPORT_PATH}"
    return REPORT_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def dept_df():
    assert CSV_PATH.exists(), f"CSV が存在しない: {CSV_PATH}"
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def test_report_exists():
    assert REPORT_PATH.exists(), f"analysis_report.md が存在しない: {REPORT_PATH}"


def test_dept_csv_exists():
    assert CSV_PATH.exists(), f"dept_summary_202401.csv が存在しない: {CSV_PATH}"


def test_report_contains_labor_cost(report_text):
    assert "人件費" in report_text, "レポートに「人件費」が含まれない"


def test_report_contains_variance(report_text):
    assert "差異" in report_text or "予算" in report_text, \
        "レポートに「差異」または「予算」が含まれない"


def test_report_has_insight_section(report_text):
    assert "インサイト" in report_text or "まとめ" in report_text, \
        "レポートにインサイトまたはまとめセクションがない"


def test_report_has_numbers(report_text):
    assert bool(re.search(r"\d+", report_text)), "レポートに数値が含まれない"


def test_dept_csv_row_count(dept_df):
    assert len(dept_df) >= 1, f"dept_summary_202401.csv の行数が0: {len(dept_df)}"


def test_report_has_dept_analysis(report_text):
    assert "部門" in report_text, "レポートに部門別分析が含まれない"


def test_report_has_employment_type_analysis(report_text):
    assert "雇用区分" in report_text or "雇用形態" in report_text, \
        "レポートに雇用区分別分析が含まれない"

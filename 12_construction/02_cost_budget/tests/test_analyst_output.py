# -*- coding: utf-8 -*-
"""
C-58: 分析成果物の品質テスト (7テスト以上)
"""

import re
from pathlib import Path

import pandas as pd
import pytest

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
CSV_PATH = OUTPUT_DIR / "project_summary_202401.csv"


@pytest.fixture(scope="module")
def report_text():
    assert REPORT_PATH.exists(), f"analysis_report.md が存在しない: {REPORT_PATH}"
    return REPORT_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def summary_df():
    assert CSV_PATH.exists(), f"project_summary_202401.csv が存在しない: {CSV_PATH}"
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def test_report_exists():
    assert REPORT_PATH.exists(), f"analysis_report.md が存在しない: {REPORT_PATH}"


def test_summary_csv_exists():
    assert CSV_PATH.exists(), f"project_summary_202401.csv が存在しない: {CSV_PATH}"


def test_report_contains_budget_keyword(report_text):
    assert "予算" in report_text, "レポートに「予算」が含まれない"


def test_report_contains_construction_keyword(report_text):
    assert "工事" in report_text, "レポートに「工事」が含まれない"


def test_report_contains_numbers(report_text):
    assert re.search(r"\d{3,}", report_text), "レポートに3桁以上の数値が含まれない"


def test_report_contains_insight(report_text):
    has_insight = "インサイト" in report_text or "まとめ" in report_text or "推奨" in report_text
    assert has_insight, "レポートにインサイト・まとめが含まれない"


def test_summary_csv_row_count(summary_df):
    assert len(summary_df) >= 4, f"project_summary の行数が 4 未満: {len(summary_df)}"


def test_summary_csv_required_columns(summary_df):
    needed = ["project_no", "budget_total", "actual_total", "variance_rate", "over_count"]
    missing = [c for c in needed if c not in summary_df.columns]
    assert not missing, f"project_summary に不足列: {missing}"


def test_report_contains_variance_keyword(report_text):
    assert "差異" in report_text, "レポートに「差異」が含まれない"

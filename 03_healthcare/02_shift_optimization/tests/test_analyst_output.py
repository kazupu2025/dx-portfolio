"""
test_analyst_output.py
analyze.py の出力（analysis_report.md, shift_summary_202401.csv）をテストする。
"""

import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_FILE = os.path.join(BASE_DIR, "output", "analysis_report.md")
SUMMARY_FILE = os.path.join(BASE_DIR, "output", "shift_summary_202401.csv")
CLEANED_FILE = os.path.join(BASE_DIR, "output", "cleaned_shift_202401.csv")


@pytest.fixture(scope="module")
def report_text():
    assert os.path.isfile(REPORT_FILE), f"レポートが存在しません: {REPORT_FILE}"
    with open(REPORT_FILE, encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def summary():
    assert os.path.isfile(SUMMARY_FILE), f"サマリーCSVが存在しません: {SUMMARY_FILE}"
    return pd.read_csv(SUMMARY_FILE, encoding="utf-8-sig")


def test_report_exists():
    assert os.path.isfile(REPORT_FILE)


def test_summary_exists():
    assert os.path.isfile(SUMMARY_FILE)


def test_report_contains_night_keyword(report_text):
    assert "夜勤" in report_text


def test_report_contains_staff_keyword(report_text):
    assert "スタッフ" in report_text or "役職" in report_text


def test_report_contains_insight(report_text):
    keywords = ["提案", "推奨", "改善", "リスク", "インサイト"]
    assert any(kw in report_text for kw in keywords), f"インサイトキーワードなし: {keywords}"


def test_report_contains_numbers(report_text):
    import re
    assert re.search(r"\d+", report_text), "レポートに数値が含まれない"


def test_summary_staff_count(summary):
    if os.path.isfile(CLEANED_FILE):
        cleaned = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")
        n_staff = cleaned["staff_id"].nunique()
        assert len(summary) >= n_staff, f"サマリー行数({len(summary)}) < スタッフ数({n_staff})"
    else:
        assert len(summary) >= 1


def test_summary_columns(summary):
    required = ["staff_id", "name", "role", "total_days", "night_count", "off_count", "night_ratio"]
    for col in required:
        assert col in summary.columns, f"列 '{col}' が存在しない"


def test_summary_night_ratio_range(summary):
    assert (summary["night_ratio"] >= 0).all()
    assert (summary["night_ratio"] <= 1).all()

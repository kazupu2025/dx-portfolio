"""
C-33: 分析出力の品質テスト (7テスト以上)
"""

import re
from pathlib import Path

import pandas as pd
import pytest

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
CSV_PATH = OUTPUT_DIR / "channel_summary_202401.csv"


@pytest.fixture(scope="module")
def report_text():
    assert REPORT_PATH.exists(), f"レポートが存在しない: {REPORT_PATH}"
    return REPORT_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def channel_df():
    assert CSV_PATH.exists(), f"CSV が存在しない: {CSV_PATH}"
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def test_report_exists():
    assert REPORT_PATH.exists(), f"analysis_report.md が存在しない: {REPORT_PATH}"


def test_channel_csv_exists():
    assert CSV_PATH.exists(), f"channel_summary_202401.csv が存在しない: {CSV_PATH}"


def test_report_contains_saiyou(report_text):
    assert "採用" in report_text, "レポートに「採用」が含まれていない"


def test_report_contains_channel(report_text):
    assert "チャネル" in report_text, "レポートに「チャネル」が含まれていない"


def test_report_contains_insight(report_text):
    assert "インサイト" in report_text or "まとめ" in report_text, \
        "レポートにインサイト/まとめセクションが含まれていない"


def test_report_contains_number(report_text):
    has_number = bool(re.search(r"\d+", report_text))
    assert has_number, "レポートに数値が含まれていない"


def test_channel_csv_row_count(channel_df):
    assert len(channel_df) >= 1, f"channel_summary_202401.csv の行数が不足: {len(channel_df)}"


def test_report_contains_jobtype(report_text):
    assert "職種" in report_text or "job_type" in report_text.lower(), \
        "レポートに職種別分析が含まれていない"


def test_report_contains_funnel(report_text):
    assert "ファネル" in report_text or "フェーズ" in report_text, \
        "レポートにファネル/フェーズ分析が含まれていない"

"""
C-22 テスト: analyze.py 出力チェック
"""
import re
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
REPORT_PATH = BASE_DIR / "output" / "analysis_report.md"
CSV_PATH = BASE_DIR / "output" / "driver_summary_202401.csv"


def test_report_exists():
    assert REPORT_PATH.exists(), f"Report not found: {REPORT_PATH}"


def test_csv_exists():
    assert CSV_PATH.exists(), f"Summary CSV not found: {CSV_PATH}"


def test_report_contains_confinement():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert "拘束" in text, "Report missing '拘束'"


def test_report_contains_violation():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert "違反" in text, "Report missing '違反'"


def test_report_contains_insight():
    text = REPORT_PATH.read_text(encoding="utf-8")
    has_insight = "インサイト" in text or "改善" in text or "提案" in text
    assert has_insight, "Report missing insight/proposal section"


def test_report_contains_numbers():
    text = REPORT_PATH.read_text(encoding="utf-8")
    has_num = bool(re.search(r"\d{2,}", text))
    assert has_num, "Report missing numerical values"


def test_csv_row_count():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    assert len(df) >= 1, f"Expected >= 1 rows, got {len(df)}"


def test_report_contains_office():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert "営業所" in text, "Report missing '営業所'"


def test_report_contains_operation_type():
    text = REPORT_PATH.read_text(encoding="utf-8")
    has_op = "運行区分" in text or "長距離" in text or "市内" in text
    assert has_op, "Report missing operation type information"


def test_summary_csv_required_cols():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    required = ["driver_id", "name", "office", "total_rides", "violation_count", "violation_rate"]
    missing = [c for c in required if c not in df.columns]
    assert not missing, f"Missing columns in summary CSV: {missing}"

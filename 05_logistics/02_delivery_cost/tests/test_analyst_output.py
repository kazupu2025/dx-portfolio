"""
C-17 テスト: analyze.py 出力チェック
"""
import re
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
REPORT_PATH = BASE_DIR / "output" / "analysis_report.md"
CSV_PATH = BASE_DIR / "output" / "cost_analysis_202401.csv"


def test_report_exists():
    assert REPORT_PATH.exists(), f"Report not found: {REPORT_PATH}"


def test_csv_exists():
    assert CSV_PATH.exists(), f"Analysis CSV not found: {CSV_PATH}"


def test_report_contains_route():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert "ルート" in text, "Report missing 'ルート'"


def test_report_contains_cost():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert "コスト" in text, "Report missing 'コスト'"


def test_report_contains_insight():
    text = REPORT_PATH.read_text(encoding="utf-8")
    has_insight = "インサイト" in text or "提案" in text or "改善" in text
    assert has_insight, "Report missing insight/proposal section"


def test_report_contains_numbers():
    text = REPORT_PATH.read_text(encoding="utf-8")
    has_num = bool(re.search(r"[¥￥]\d[\d,]*", text) or re.search(r"\d{4,}", text))
    assert has_num, "Report missing numerical values"


def test_csv_row_count():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    assert len(df) >= 1, f"Expected >= 1 rows, got {len(df)}"


def test_report_contains_vehicle():
    text = REPORT_PATH.read_text(encoding="utf-8")
    has_vehicle = "車種" in text or "トラック" in text or "軽バン" in text
    assert has_vehicle, "Report missing vehicle information"


def test_report_contains_monthly():
    text = REPORT_PATH.read_text(encoding="utf-8")
    has_monthly = "月間" in text or "2024" in text
    assert has_monthly, "Report missing monthly cost information"

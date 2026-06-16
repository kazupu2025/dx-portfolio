import pandas as pd
import pytest
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
REPORT_PATH = BASE_DIR / "output" / "analysis_report.md"
SUMMARY_PATH = BASE_DIR / "output" / "variance_summary_202401.csv"

def test_report_exists():
    assert REPORT_PATH.exists()

def test_summary_exists():
    assert SUMMARY_PATH.exists()

def test_report_contains_diff():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert "差異" in text

def test_report_contains_cost():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert "材料費" in text or "コスト" in text

def test_summary_row_count():
    df = pd.read_csv(SUMMARY_PATH, encoding="utf-8-sig")
    assert len(df) >= 1

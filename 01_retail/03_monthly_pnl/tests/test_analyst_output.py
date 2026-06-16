"""
C-19: tests/test_analyst_output.py
analysis_report.md と pnl_summary_202401.csv のテスト
"""
import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_FILE = os.path.join(BASE_DIR, "output", "analysis_report.md")
SUMMARY_FILE = os.path.join(BASE_DIR, "output", "pnl_summary_202401.csv")


def test_report_exists():
    assert os.path.isfile(REPORT_FILE), f"File not found: {REPORT_FILE}"


def test_report_contains_revenue():
    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    assert "売上" in content


def test_report_contains_profit():
    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    assert "粗利" in content or "利益" in content


def test_report_contains_insight():
    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    assert "インサイト" in content or "所見" in content


def test_summary_csv_exists():
    assert os.path.isfile(SUMMARY_FILE), f"File not found: {SUMMARY_FILE}"


def test_summary_csv_row_count():
    df = pd.read_csv(SUMMARY_FILE, encoding="utf-8-sig")
    assert len(df) >= 1, f"Expected >= 1 rows, got {len(df)}"


def test_summary_csv_columns():
    df = pd.read_csv(SUMMARY_FILE, encoding="utf-8-sig")
    required = ["store_id", "store_name", "planned_revenue", "actual_revenue"]
    for col in required:
        assert col in df.columns, f"Missing column: {col}"

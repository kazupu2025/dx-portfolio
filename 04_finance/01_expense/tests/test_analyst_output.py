import pytest
from pathlib import Path

REPORT = Path("output/analysis_report.md")

@pytest.fixture(scope="module")
def report(): return REPORT.read_text(encoding="utf-8")

def test_report_exists(): assert REPORT.exists()
def test_report_has_dept_section(report): assert "部門" in report
def test_report_has_budget_section(report): assert "予算" in report
def test_report_has_expense_type_section(report): assert "費目" in report
def test_report_has_alert_marker(report): assert "%" in report
def test_report_has_anomaly_section(report): assert "異常" in report or "検出" in report

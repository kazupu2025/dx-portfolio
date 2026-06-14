import pytest
from pathlib import Path

REPORT = Path("output/analysis_report.md")

@pytest.fixture(scope="module")
def report(): return REPORT.read_text(encoding="utf-8")

def test_report_exists(): assert REPORT.exists()
def test_report_has_process_section(report): assert "工程" in report
def test_report_has_defect_section(report): assert "不良率" in report
def test_report_has_anomaly_section(report): assert "異常値" in report or "検出" in report
def test_report_has_percent(report): assert "%" in report
def test_report_has_insight(report): assert "インサイト" in report or "ビジネス" in report

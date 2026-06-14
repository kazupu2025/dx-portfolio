import pytest
from pathlib import Path

REPORT = Path(__file__).parent.parent / "output" / "analysis_report.md"


@pytest.fixture(scope="module")
def report(): return REPORT.read_text(encoding="utf-8")


def test_report_exists(): assert REPORT.exists()
def test_report_has_hourly_section(report): assert "時間帯" in report
def test_report_has_dept_section(report): assert "診療科" in report
def test_report_has_peak_marker(report): assert "ピーク" in report
def test_report_has_wait_section(report): assert "待ち" in report
def test_report_has_insight(report): assert "インサイト" in report or "ビジネス" in report

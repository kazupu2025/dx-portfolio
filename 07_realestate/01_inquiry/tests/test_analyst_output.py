import pytest
from pathlib import Path

BASE = Path(__file__).parent.parent
REPORT = BASE / "output" / "analysis_report.md"

@pytest.fixture(scope="module")
def report(): return REPORT.read_text(encoding="utf-8")

def test_report_exists(): assert REPORT.exists()
def test_report_has_funnel(report): assert "ファネル" in report
def test_report_has_area_section(report): assert "エリア" in report
def test_report_has_agent_section(report): assert "担当者" in report
def test_report_has_rate(report): assert "成約率" in report
def test_report_has_insight(report): assert "インサイト" in report or "ビジネス" in report

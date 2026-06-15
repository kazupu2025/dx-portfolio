import pytest
from pathlib import Path

REPORT = Path(__file__).parent.parent / "output" / "analysis_report.md"

@pytest.fixture(scope="module")
def report(): return REPORT.read_text(encoding="utf-8")

def test_report_exists(): assert REPORT.exists()
def test_report_has_area(report): assert "エリア" in report
def test_report_has_vacancy(report): assert "空室率" in report
def test_report_has_revenue(report): assert "収益" in report
def test_report_has_insight(report): assert "インサイト" in report or "ビジネス" in report
def test_report_has_kpi(report): assert "KPI" in report or "総物件数" in report

import pytest
from pathlib import Path

REPORT = Path("output/analysis_report.md")

@pytest.fixture(scope="module")
def report():
    return REPORT.read_text(encoding="utf-8")

def test_report_exists():
    assert REPORT.exists()

def test_report_has_store_section(report):
    assert "店舗" in report

def test_report_has_daily_section(report):
    assert "日次" in report or "日別" in report

def test_report_has_waste_section(report):
    assert "廃棄ロス率" in report

def test_report_has_alert_marker(report):
    assert "%" in report

def test_report_has_anomaly_section(report):
    assert "異常" in report or "アノマリ" in report or "検出" in report

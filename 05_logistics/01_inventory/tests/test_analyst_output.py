import pytest
from pathlib import Path

REPORT = Path("output/analysis_report.md")


@pytest.fixture(scope="module")
def report():
    return REPORT.read_text(encoding="utf-8")

def test_report_exists():
    assert REPORT.exists()

def test_report_has_warehouse_section(report):
    assert "倉庫" in report

def test_report_has_stockout_section(report):
    assert "欠品" in report

def test_report_has_turnover_section(report):
    assert "回転率" in report

def test_report_has_alert_marker(report):
    assert "%" in report

def test_report_has_anomaly_section(report):
    assert "異常" in report or "検出" in report

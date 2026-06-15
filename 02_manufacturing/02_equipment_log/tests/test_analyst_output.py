"""
B-09 分析レポート出力テスト (6テスト)
"""
import pytest
from pathlib import Path

BASE   = Path(__file__).parent.parent
OUT    = BASE / "output"
REPORT = OUT / "analysis_report.md"
ANOMALY_CSV = OUT / "anomaly_sensor_202401.csv"


@pytest.fixture(scope="module")
def report_content():
    assert REPORT.exists(), f"{REPORT} が存在しない"
    with open(REPORT, encoding="utf-8") as f:
        return f.read()


def test_report_exists():
    assert REPORT.exists()


def test_report_has_equipment(report_content):
    assert "設備" in report_content


def test_report_has_alert_keyword(report_content):
    assert any(kw in report_content for kw in ["CRITICAL", "WARNING", "アラート"])


def test_report_has_insight(report_content):
    assert "インサイト" in report_content


def test_anomaly_csv_exists():
    assert ANOMALY_CSV.exists()


def test_report_has_precursor_or_maintenance(report_content):
    assert any(kw in report_content for kw in ["予兆", "メンテナンス"])

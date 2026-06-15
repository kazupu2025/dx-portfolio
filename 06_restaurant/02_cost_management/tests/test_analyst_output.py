import pytest
from pathlib import Path

REPORT = Path("output/analysis_report.md")


@pytest.fixture(scope="module")
def report():
    return REPORT.read_text(encoding="utf-8")


def test_report_exists():
    assert REPORT.exists()


def test_report_has_category(report):
    assert "カテゴリ" in report


def test_report_has_store(report):
    assert "店舗" in report


def test_report_has_waste(report):
    assert "廃棄" in report


def test_report_has_loss_rate(report):
    assert "ロス率" in report


def test_report_has_insight(report):
    assert "インサイト" in report or "ビジネス" in report

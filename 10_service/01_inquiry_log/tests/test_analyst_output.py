"""
B-15 分析レポートテスト (6テスト)
"""
import pytest
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RPT_PATH = BASE / "output" / "analysis_report.md"


@pytest.fixture(scope="module")
def report():
    assert RPT_PATH.exists(), f"Report not found: {RPT_PATH}"
    with open(RPT_PATH, encoding="utf-8") as f:
        return f.read()


def test_report_exists():
    assert RPT_PATH.exists()


def test_contains_category(report):
    assert "カテゴリ" in report


def test_contains_operator(report):
    assert "担当者" in report


def test_contains_response_time(report):
    assert "対応時間" in report


def test_contains_insight(report):
    assert "インサイト" in report


def test_contains_resolution_rate(report):
    assert "解決率" in report

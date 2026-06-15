"""
B-11 テスト: 分析レポート出力検証（6テスト）
"""
import pytest
from pathlib import Path

BASE = Path(__file__).parent.parent
REPORT_PATH = BASE / "output" / "credit_report_202401.txt"


@pytest.fixture(scope="module")
def report_text():
    assert REPORT_PATH.exists(), f"レポートが存在しません: {REPORT_PATH}"
    return REPORT_PATH.read_text(encoding="utf-8")


def test_report_exists():
    assert REPORT_PATH.exists(), f"Report not found: {REPORT_PATH}"


def test_all_areas(report_text):
    areas = ["リスク分類", "職業", "申込用途", "負債比率", "スコア分布", "インサイト"]
    missing = [a for a in areas if a not in report_text]
    assert missing == [], f"不足エリア: {missing}"


def test_score_keyword(report_text):
    assert "スコア" in report_text


def test_risk_keyword(report_text):
    assert "リスク" in report_text


def test_insight_keyword(report_text):
    assert "インサイト" in report_text


def test_high_risk_keyword(report_text):
    assert "高リスク" in report_text

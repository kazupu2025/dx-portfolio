"""
B-11 テスト: 可視化出力検証（4テスト）
"""
import pytest
from pathlib import Path

BASE = Path(__file__).parent.parent
CHARTS = BASE / "output" / "charts"

EXPECTED_CHARTS = [
    "bar_risk_distribution.png",
    "bar_occupation_score.png",
    "hist_credit_score.png",
]


def test_charts_dir_exists():
    assert CHARTS.exists(), f"chartsディレクトリが存在しません: {CHARTS}"


def test_bar_risk_distribution():
    chart = CHARTS / "bar_risk_distribution.png"
    assert chart.exists(), f"チャートが存在しません: {chart}"


def test_bar_occupation_score():
    chart = CHARTS / "bar_occupation_score.png"
    assert chart.exists(), f"チャートが存在しません: {chart}"


def test_hist_credit_score():
    chart = CHARTS / "hist_credit_score.png"
    assert chart.exists(), f"チャートが存在しません: {chart}"

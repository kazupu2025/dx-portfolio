"""
B-15 可視化出力テスト (4テスト)
"""
import pytest
from pathlib import Path

BASE   = Path(__file__).resolve().parent.parent
CHARTS = BASE / "output" / "charts"


def test_charts_dir_exists():
    assert CHARTS.exists() and CHARTS.is_dir()


def test_chart_category_exists():
    assert (CHARTS / "bar_category_inquiry.png").exists()


def test_chart_operator_exists():
    assert (CHARTS / "bar_operator_performance.png").exists()


def test_chart_hourly_exists():
    assert (CHARTS / "bar_hourly_inquiry.png").exists()

# -*- coding: utf-8 -*-
"""
C-54: 可視化出力テスト（3テスト以上）
"""

import pytest
from pathlib import Path

CHARTS_DIR = Path(__file__).parent.parent / "output" / "charts"

EXPECTED_CHARTS = [
    "bar_store_revenue.png",
    "bar_store_margin.png",
    "bar_cost_breakdown.png",
]


# 1. charts ディレクトリが存在すること
def test_charts_dir_exists():
    assert CHARTS_DIR.exists(), f"charts ディレクトリが見つかりません: {CHARTS_DIR}"


# 2. 全グラフファイルが存在すること
@pytest.mark.parametrize("chart_name", EXPECTED_CHARTS)
def test_chart_file_exists(chart_name):
    chart_path = CHARTS_DIR / chart_name
    assert chart_path.exists(), f"グラフファイルが見つかりません: {chart_path}"


# 3. 全グラフファイルのサイズが1KB以上
@pytest.mark.parametrize("chart_name", EXPECTED_CHARTS)
def test_chart_file_size(chart_name):
    chart_path = CHARTS_DIR / chart_name
    if chart_path.exists():
        size = chart_path.stat().st_size
        assert size >= 1024, f"グラフファイルが小さすぎる ({size} bytes): {chart_path}"

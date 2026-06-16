# -*- coding: utf-8 -*-
"""
test_viz_output.py
output/charts/ グラフファイルのテスト（4テスト以上）
"""

import pytest
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CHARTS_DIR = BASE_DIR / "output" / "charts"

EXPECTED_CHARTS = [
    "bar_segment_count.png",
    "scatter_rfm_frequency_monetary.png",
    "bar_category_amount.png",
]


# 1. charts ディレクトリの存在確認
def test_charts_dir_exists():
    assert CHARTS_DIR.exists(), f"charts ディレクトリが存在しません: {CHARTS_DIR}"


# 2. bar_segment_count.png の存在確認
def test_bar_segment_count_exists():
    f = CHARTS_DIR / "bar_segment_count.png"
    assert f.exists(), f"グラフが存在しません: {f}"


# 3. scatter_rfm_frequency_monetary.png の存在確認
def test_scatter_rfm_exists():
    f = CHARTS_DIR / "scatter_rfm_frequency_monetary.png"
    assert f.exists(), f"グラフが存在しません: {f}"


# 4. bar_category_amount.png の存在確認
def test_bar_category_amount_exists():
    f = CHARTS_DIR / "bar_category_amount.png"
    assert f.exists(), f"グラフが存在しません: {f}"


# 5. 全グラフのファイルサイズ > 0
@pytest.mark.parametrize("chart_name", EXPECTED_CHARTS)
def test_chart_file_size_positive(chart_name):
    f = CHARTS_DIR / chart_name
    if not f.exists():
        pytest.skip(f"グラフが存在しないためスキップ: {f}")
    assert f.stat().st_size > 0, f"グラフのファイルサイズが 0 です: {f}"

"""
C-23: 可視化出力の品質テスト
"""

from pathlib import Path

import pytest

BASE_DIR = Path(__file__).parent.parent
CHARTS_DIR = BASE_DIR / "output" / "charts"

EXPECTED_CHARTS = [
    "bar_area_cost.png",
    "bar_property_cost_top10.png",
    "pie_cost_category.png",
]


def test_charts_dir_exists():
    assert CHARTS_DIR.exists(), f"charts ディレクトリが存在しない: {CHARTS_DIR}"


@pytest.mark.parametrize("chart_name", EXPECTED_CHARTS)
def test_chart_exists(chart_name):
    path = CHARTS_DIR / chart_name
    assert path.exists(), f"グラフファイルが存在しない: {path}"


@pytest.mark.parametrize("chart_name", EXPECTED_CHARTS)
def test_chart_size(chart_name):
    path = CHARTS_DIR / chart_name
    if path.exists():
        size = path.stat().st_size
        assert size > 1024, f"グラフファイルが小さすぎる({size} bytes): {chart_name}"


def test_minimum_chart_count():
    if CHARTS_DIR.exists():
        png_files = list(CHARTS_DIR.glob("*.png"))
        assert len(png_files) >= 3, f"グラフが3枚未満: {len(png_files)} 枚"

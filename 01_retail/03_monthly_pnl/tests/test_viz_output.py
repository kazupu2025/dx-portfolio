"""
C-19: tests/test_viz_output.py
output/charts/ 各 PNG の存在確認
"""
import os
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS_DIR = os.path.join(BASE_DIR, "output", "charts")

EXPECTED_CHARTS = [
    "bar_store_revenue_vs_plan.png",
    "bar_store_profit_flag.png",
    "line_monthly_profit.png",
]


@pytest.mark.parametrize("filename", EXPECTED_CHARTS)
def test_chart_exists(filename):
    path = os.path.join(CHARTS_DIR, filename)
    assert os.path.isfile(path), f"Chart not found: {path}"


def test_charts_dir_exists():
    assert os.path.isdir(CHARTS_DIR), f"Charts directory not found: {CHARTS_DIR}"


def test_minimum_chart_count():
    """3枚以上の PNG が生成されていること"""
    if not os.path.isdir(CHARTS_DIR):
        pytest.fail(f"Charts directory not found: {CHARTS_DIR}")
    pngs = [f for f in os.listdir(CHARTS_DIR) if f.endswith(".png")]
    assert len(pngs) >= 3, f"Expected >= 3 PNGs, found {len(pngs)}"

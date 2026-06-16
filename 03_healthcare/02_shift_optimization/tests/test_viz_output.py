"""
test_viz_output.py
visualize.py の出力（charts/*.png）の存在を確認する。
"""

import os
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS_DIR = os.path.join(BASE_DIR, "output", "charts")

EXPECTED_CHARTS = [
    "bar_role_night_ratio.png",
    "bar_staff_night_count.png",
    "stacked_shift_distribution.png",
]


def test_charts_dir_exists():
    assert os.path.isdir(CHARTS_DIR), f"charts/ ディレクトリが存在しません: {CHARTS_DIR}"


@pytest.mark.parametrize("filename", EXPECTED_CHARTS)
def test_chart_file_exists(filename):
    path = os.path.join(CHARTS_DIR, filename)
    assert os.path.isfile(path), f"チャートが存在しません: {path}"


@pytest.mark.parametrize("filename", EXPECTED_CHARTS)
def test_chart_file_not_empty(filename):
    path = os.path.join(CHARTS_DIR, filename)
    if os.path.isfile(path):
        assert os.path.getsize(path) > 1024, f"チャートファイルが小さすぎます: {path}"


def test_at_least_3_charts():
    if not os.path.isdir(CHARTS_DIR):
        pytest.skip("charts/ ディレクトリが存在しません")
    pngs = [f for f in os.listdir(CHARTS_DIR) if f.endswith(".png")]
    assert len(pngs) >= 3, f"PNG が3枚未満: {pngs}"

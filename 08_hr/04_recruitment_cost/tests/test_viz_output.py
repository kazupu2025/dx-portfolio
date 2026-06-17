"""
C-41: 可視化出力の品質テスト (4テスト以上)
"""

from pathlib import Path

import pytest

BASE_DIR = Path(__file__).parent.parent
CHARTS_DIR = BASE_DIR / "output" / "charts"

EXPECTED_CHARTS = [
    "bar_channel_cost.png",
    "bar_channel_hire_rate.png",
    "bar_phase_funnel.png",
]


def test_charts_dir_exists():
    assert CHARTS_DIR.exists(), f"charts ディレクトリが存在しない: {CHARTS_DIR}"


@pytest.mark.parametrize("filename", EXPECTED_CHARTS)
def test_chart_file_exists(filename):
    path = CHARTS_DIR / filename
    assert path.exists(), f"グラフファイルが存在しない: {path}"


@pytest.mark.parametrize("filename", EXPECTED_CHARTS)
def test_chart_file_size(filename):
    path = CHARTS_DIR / filename
    if path.exists():
        size = path.stat().st_size
        assert size > 0, f"グラフファイルのサイズが 0 バイト: {path}"

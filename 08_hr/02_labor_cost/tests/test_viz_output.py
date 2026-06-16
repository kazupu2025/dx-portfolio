"""
C-30: 可視化出力の品質テスト (4テスト以上)
"""

from pathlib import Path

import pytest

BASE_DIR = Path(__file__).parent.parent
CHARTS_DIR = BASE_DIR / "output" / "charts"

EXPECTED_CHARTS = [
    "bar_dept_variance.png",
    "bar_employment_cost.png",
    "line_monthly_trend.png",
]


def test_charts_dir_exists():
    assert CHARTS_DIR.exists(), f"charts ディレクトリが存在しない: {CHARTS_DIR}"


def test_all_charts_exist():
    missing = [name for name in EXPECTED_CHARTS if not (CHARTS_DIR / name).exists()]
    assert not missing, f"グラフファイルが存在しない: {missing}"


@pytest.mark.parametrize("chart_name", EXPECTED_CHARTS)
def test_chart_file_size_positive(chart_name):
    chart_path = CHARTS_DIR / chart_name
    assert chart_path.exists(), f"グラフファイルが存在しない: {chart_path}"
    assert chart_path.stat().st_size > 0, f"グラフファイルのサイズが0: {chart_path}"


def test_chart_count():
    if not CHARTS_DIR.exists():
        pytest.skip("charts ディレクトリが存在しないためスキップ")
    actual_charts = list(CHARTS_DIR.glob("*.png"))
    assert len(actual_charts) >= 3, f"グラフ数が3未満: {len(actual_charts)}"

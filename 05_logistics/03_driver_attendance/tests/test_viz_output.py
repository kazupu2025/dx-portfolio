"""
C-22 テスト: visualize.py 出力チェック
"""
import pytest
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CHARTS_DIR = BASE_DIR / "output" / "charts"

EXPECTED_CHARTS = [
    "bar_office_violation_rate.png",
    "bar_driver_violation_top10.png",
    "pie_operation_distance.png",
]


def test_charts_dir_exists():
    assert CHARTS_DIR.exists(), f"Charts directory not found: {CHARTS_DIR}"


@pytest.mark.parametrize("chart_name", EXPECTED_CHARTS)
def test_chart_exists(chart_name):
    path = CHARTS_DIR / chart_name
    assert path.exists(), f"Chart not found: {path}"


@pytest.mark.parametrize("chart_name", EXPECTED_CHARTS)
def test_chart_not_empty(chart_name):
    path = CHARTS_DIR / chart_name
    if path.exists():
        size = path.stat().st_size
        assert size > 1000, f"Chart file too small ({size} bytes): {chart_name}"


def test_minimum_chart_count():
    charts = list(CHARTS_DIR.glob("*.png")) if CHARTS_DIR.exists() else []
    assert len(charts) >= 3, f"Expected >= 3 charts, found {len(charts)}"

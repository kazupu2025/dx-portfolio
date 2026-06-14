import pytest
from pathlib import Path

CHARTS = Path(__file__).parent.parent / "output" / "charts"


def test_charts_dir_exists(): assert CHARTS.exists()
def test_bar_hourly_exists(): assert (CHARTS / "bar_hourly_visits.png").exists()
def test_bar_dept_exists(): assert (CHARTS / "bar_dept_visits.png").exists()
def test_heatmap_exists(): assert (CHARTS / "heatmap_weekday_hour.png").exists()

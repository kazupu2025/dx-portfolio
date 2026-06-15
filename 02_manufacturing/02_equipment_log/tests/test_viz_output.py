"""
B-09 可視化出力テスト (4テスト)
"""
import pytest
from pathlib import Path

BASE   = Path(__file__).parent.parent
CHARTS = BASE / "output" / "charts"
EXPECTED_CHARTS = [
    "line_equipment_temperature.png",
    "bar_equipment_alert_count.png",
    "heatmap_equipment_sensor_z.png",
]


def test_charts_dir_exists():
    assert CHARTS.exists()


def test_temperature_chart_exists():
    assert (CHARTS / "line_equipment_temperature.png").exists()


def test_alert_bar_chart_exists():
    assert (CHARTS / "bar_equipment_alert_count.png").exists()


def test_heatmap_chart_exists():
    assert (CHARTS / "heatmap_equipment_sensor_z.png").exists()

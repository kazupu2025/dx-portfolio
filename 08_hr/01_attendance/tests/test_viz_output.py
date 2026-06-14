import pytest
from pathlib import Path

CHARTS = Path("output/charts")


def test_charts_dir_exists():
    assert CHARTS.exists()


def test_bar_dept_overtime_exists():
    assert (CHARTS / "bar_dept_overtime.png").exists()


def test_bar_overtime_alert_exists():
    assert (CHARTS / "bar_overtime_alert.png").exists()


def test_line_daily_attendance_exists():
    assert (CHARTS / "line_daily_attendance.png").exists()

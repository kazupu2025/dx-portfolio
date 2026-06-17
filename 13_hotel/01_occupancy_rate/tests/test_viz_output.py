# -*- coding: utf-8 -*-
import os
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS_DIR = os.path.join(BASE_DIR, "output", "charts")


def test_revenue_chart_exists():
    path = os.path.join(CHARTS_DIR, "bar_roomtype_revenue.png")
    assert os.path.exists(path), "bar_roomtype_revenue.png not found"


def test_cancel_rate_chart_exists():
    path = os.path.join(CHARTS_DIR, "bar_roomtype_cancel_rate.png")
    assert os.path.exists(path), "bar_roomtype_cancel_rate.png not found"


def test_daily_occupancy_chart_exists():
    path = os.path.join(CHARTS_DIR, "line_daily_occupancy.png")
    assert os.path.exists(path), "line_daily_occupancy.png not found"

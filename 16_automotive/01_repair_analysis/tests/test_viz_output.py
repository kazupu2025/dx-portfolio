# -*- coding: utf-8 -*-
import os
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS_DIR = os.path.join(BASE_DIR, "output", "charts")

def test_shop_revenue_chart_exists():
    path = os.path.join(CHARTS_DIR, "bar_shop_revenue.png")
    assert os.path.exists(path), f"Missing chart: {path}"

def test_worktype_delay_chart_exists():
    path = os.path.join(CHARTS_DIR, "bar_worktype_delay.png")
    assert os.path.exists(path), f"Missing chart: {path}"

def test_tech_efficiency_chart_exists():
    path = os.path.join(CHARTS_DIR, "bar_tech_efficiency.png")
    assert os.path.exists(path), f"Missing chart: {path}"

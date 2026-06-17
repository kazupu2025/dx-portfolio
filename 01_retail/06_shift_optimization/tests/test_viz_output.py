# -*- coding: utf-8 -*-
import os
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS_DIR = os.path.join(BASE_DIR, "output", "charts")


def test_bar_store_labor_cost_exists():
    path = os.path.join(CHARTS_DIR, "bar_store_labor_cost.png")
    assert os.path.exists(path), f"Missing: {path}"


def test_bar_role_avg_wage_exists():
    path = os.path.join(CHARTS_DIR, "bar_role_avg_wage.png")
    assert os.path.exists(path), f"Missing: {path}"


def test_bar_store_gap_exists():
    path = os.path.join(CHARTS_DIR, "bar_store_gap.png")
    assert os.path.exists(path), f"Missing: {path}"

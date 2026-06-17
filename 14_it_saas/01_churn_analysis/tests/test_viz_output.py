# -*- coding: utf-8 -*-
import os
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS_DIR = os.path.join(BASE_DIR, "output", "charts")


def test_bar_plan_churn_rate_exists():
    path = os.path.join(CHARTS_DIR, "bar_plan_churn_rate.png")
    assert os.path.exists(path), f"Chart not found: {path}"


def test_bar_industry_ltv_exists():
    path = os.path.join(CHARTS_DIR, "bar_industry_ltv.png")
    assert os.path.exists(path), f"Chart not found: {path}"


def test_bar_churn_risk_exists():
    path = os.path.join(CHARTS_DIR, "bar_churn_risk.png")
    assert os.path.exists(path), f"Chart not found: {path}"

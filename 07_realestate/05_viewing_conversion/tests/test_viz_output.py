# -*- coding: utf-8 -*-
import os
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS_DIR = os.path.join(BASE_DIR, "output", "charts")


def test_bar_type_conversion_exists():
    path = os.path.join(CHARTS_DIR, "bar_type_conversion.png")
    assert os.path.exists(path), f"Chart not found: {path}"


def test_bar_area_visit_exists():
    path = os.path.join(CHARTS_DIR, "bar_area_visit.png")
    assert os.path.exists(path), f"Chart not found: {path}"


def test_bar_price_tier_count_exists():
    path = os.path.join(CHARTS_DIR, "bar_price_tier_count.png")
    assert os.path.exists(path), f"Chart not found: {path}"

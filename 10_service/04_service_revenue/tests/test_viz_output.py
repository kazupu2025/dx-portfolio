# -*- coding: utf-8 -*-
"""
pytest: visualize.py 出力チェック (3テスト)
"""

import os
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CHARTS_DIR = os.path.join(BASE_DIR, "output", "charts")


def test_bar_service_revenue_png():
    path = os.path.join(CHARTS_DIR, "bar_service_revenue.png")
    assert os.path.exists(path), f"File not found: {path}"
    assert os.path.getsize(path) > 0, "File is empty"


def test_bar_service_margin_png():
    path = os.path.join(CHARTS_DIR, "bar_service_margin.png")
    assert os.path.exists(path), f"File not found: {path}"
    assert os.path.getsize(path) > 0, "File is empty"


def test_bar_category_profit_png():
    path = os.path.join(CHARTS_DIR, "bar_category_profit.png")
    assert os.path.exists(path), f"File not found: {path}"
    assert os.path.getsize(path) > 0, "File is empty"

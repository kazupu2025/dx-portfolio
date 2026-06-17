# -*- coding: utf-8 -*-
"""
C-49 可視化出力テスト (3テスト以上)
"""

import os
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CHARTS_DIR = os.path.join(BASE_DIR, "output", "charts")


def test_bar_farm_harvest_exists():
    path = os.path.join(CHARTS_DIR, "bar_farm_harvest.png")
    assert os.path.exists(path), f"File not found: {path}"


def test_bar_crop_grade_a_rate_exists():
    path = os.path.join(CHARTS_DIR, "bar_crop_grade_a_rate.png")
    assert os.path.exists(path), f"File not found: {path}"


def test_bar_quality_flag_dist_exists():
    path = os.path.join(CHARTS_DIR, "bar_quality_flag_dist.png")
    assert os.path.exists(path), f"File not found: {path}"


def test_chart_files_not_empty():
    for fname in ["bar_farm_harvest.png", "bar_crop_grade_a_rate.png", "bar_quality_flag_dist.png"]:
        path = os.path.join(CHARTS_DIR, fname)
        if os.path.exists(path):
            assert os.path.getsize(path) > 0, f"Empty file: {fname}"

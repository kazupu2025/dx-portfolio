# -*- coding: utf-8 -*-
"""
C-59 可視化出力テスト (3テスト以上)
"""

import os
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CHARTS_DIR = os.path.join(BASE_DIR, "output", "charts")


def test_bar_crop_achievement_exists():
    path = os.path.join(CHARTS_DIR, "bar_crop_achievement.png")
    assert os.path.exists(path), f"File not found: {path}"


def test_bar_worktype_productivity_exists():
    path = os.path.join(CHARTS_DIR, "bar_worktype_productivity.png")
    assert os.path.exists(path), f"File not found: {path}"


def test_bar_staff_productivity_exists():
    path = os.path.join(CHARTS_DIR, "bar_staff_productivity.png")
    assert os.path.exists(path), f"File not found: {path}"


def test_chart_files_not_empty():
    for fname in ["bar_crop_achievement.png", "bar_worktype_productivity.png", "bar_staff_productivity.png"]:
        path = os.path.join(CHARTS_DIR, fname)
        if os.path.exists(path):
            assert os.path.getsize(path) > 0, f"Empty file: {fname}"

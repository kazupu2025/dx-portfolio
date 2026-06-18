# -*- coding: utf-8 -*-
import os
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")


def test_bar_type_utilization_exists():
    path = os.path.join(CHARTS_DIR, "bar_type_utilization.png")
    assert os.path.exists(path), "bar_type_utilization.png must exist"


def test_bar_dept_absence_exists():
    path = os.path.join(CHARTS_DIR, "bar_dept_absence.png")
    assert os.path.exists(path), "bar_dept_absence.png must exist"


def test_bar_type_overtime_exists():
    path = os.path.join(CHARTS_DIR, "bar_type_overtime.png")
    assert os.path.exists(path), "bar_type_overtime.png must exist"

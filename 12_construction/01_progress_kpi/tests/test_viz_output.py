# -*- coding: utf-8 -*-
import os
import pytest

CHART_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "charts")

def test_bar_site_progress_exists():
    path = os.path.join(CHART_DIR, "bar_site_progress.png")
    assert os.path.exists(path), f"bar_site_progress.png が存在しない: {path}"

def test_bar_process_efficiency_exists():
    path = os.path.join(CHART_DIR, "bar_process_efficiency.png")
    assert os.path.exists(path), f"bar_process_efficiency.png が存在しない: {path}"

def test_bar_site_defect_exists():
    path = os.path.join(CHART_DIR, "bar_site_defect.png")
    assert os.path.exists(path), f"bar_site_defect.png が存在しない: {path}"

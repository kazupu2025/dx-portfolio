# -*- coding: utf-8 -*-
import os
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS_DIR = os.path.join(BASE_DIR, "output", "charts")


def test_zone_processed_chart_exists():
    path = os.path.join(CHARTS_DIR, "bar_zone_processed.png")
    assert os.path.exists(path), f"File not found: {path}"


def test_task_throughput_chart_exists():
    path = os.path.join(CHARTS_DIR, "bar_task_throughput.png")
    assert os.path.exists(path), f"File not found: {path}"


def test_worker_error_top10_chart_exists():
    path = os.path.join(CHARTS_DIR, "bar_worker_error_top10.png")
    assert os.path.exists(path), f"File not found: {path}"

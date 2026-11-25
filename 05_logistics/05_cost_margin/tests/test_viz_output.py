# -*- coding: utf-8 -*-
"""可視化出力テスト (3テスト以上)"""
import pytest
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CHARTS_DIR = BASE_DIR / "output" / "charts"


def test_bar_type_margin_exists():
    chart_path = CHARTS_DIR / "bar_type_margin.png"
    assert chart_path.exists(), f"bar_type_margin.png が存在しない: {chart_path}"


def test_bar_area_profit_exists():
    chart_path = CHARTS_DIR / "bar_area_profit.png"
    assert chart_path.exists(), f"bar_area_profit.png が存在しない: {chart_path}"


def test_bar_vehicle_cpkm_exists():
    chart_path = CHARTS_DIR / "bar_vehicle_cpkm.png"
    assert chart_path.exists(), f"bar_vehicle_cpkm.png が存在しない: {chart_path}"


def test_charts_dir_exists():
    assert CHARTS_DIR.exists(), f"charts ディレクトリが存在しない: {CHARTS_DIR}"

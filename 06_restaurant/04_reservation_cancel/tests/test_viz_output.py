# -*- coding: utf-8 -*-
"""
C-38: 可視化出力テスト (4テスト以上)
"""

import pytest
from pathlib import Path

CHARTS_DIR = Path(__file__).parent.parent / "output" / "charts"

EXPECTED_CHARTS = [
    "bar_store_cancel_rate.png",
    "bar_cancel_reason.png",
    "bar_weekday_cancel.png",
]


def test_01_charts_dir_exists():
    """output/charts ディレクトリが存在する"""
    assert CHARTS_DIR.exists(), f"Charts dir not found: {CHARTS_DIR}"


def test_02_store_cancel_rate_chart_exists():
    """bar_store_cancel_rate.png が存在する"""
    path = CHARTS_DIR / "bar_store_cancel_rate.png"
    assert path.exists(), f"Chart not found: {path}"


def test_03_cancel_reason_chart_exists():
    """bar_cancel_reason.png が存在する"""
    path = CHARTS_DIR / "bar_cancel_reason.png"
    assert path.exists(), f"Chart not found: {path}"


def test_04_weekday_cancel_chart_exists():
    """bar_weekday_cancel.png が存在する"""
    path = CHARTS_DIR / "bar_weekday_cancel.png"
    assert path.exists(), f"Chart not found: {path}"


def test_05_charts_are_non_empty():
    """全チャートファイルのサイズが0より大きい"""
    for name in EXPECTED_CHARTS:
        path = CHARTS_DIR / name
        if path.exists():
            assert path.stat().st_size > 0, f"Chart file is empty: {path}"


def test_06_all_expected_charts_exist():
    """期待する3枚の全チャートが存在する"""
    missing = [name for name in EXPECTED_CHARTS if not (CHARTS_DIR / name).exists()]
    assert missing == [], f"Missing charts: {missing}"

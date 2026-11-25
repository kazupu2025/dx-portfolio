# -*- coding: utf-8 -*-
"""
C-58: 可視化成果物の品質テスト (3テスト以上)
"""

from pathlib import Path

import pytest

BASE_DIR = Path(__file__).parent.parent
CHARTS_DIR = BASE_DIR / "output" / "charts"

EXPECTED_CHARTS = [
    "bar_project_variance.png",
    "bar_worktype_actual.png",
    "bar_category_budget_actual.png",
]


def test_charts_dir_exists():
    assert CHARTS_DIR.exists(), f"charts ディレクトリが存在しない: {CHARTS_DIR}"


def test_bar_project_variance_exists():
    path = CHARTS_DIR / "bar_project_variance.png"
    assert path.exists(), f"グラフが存在しない: {path}"


def test_bar_worktype_actual_exists():
    path = CHARTS_DIR / "bar_worktype_actual.png"
    assert path.exists(), f"グラフが存在しない: {path}"


def test_bar_category_budget_actual_exists():
    path = CHARTS_DIR / "bar_category_budget_actual.png"
    assert path.exists(), f"グラフが存在しない: {path}"


def test_chart_files_not_empty():
    for name in EXPECTED_CHARTS:
        path = CHARTS_DIR / name
        if path.exists():
            assert path.stat().st_size > 1000, f"グラフファイルが小さすぎる: {name} ({path.stat().st_size} bytes)"

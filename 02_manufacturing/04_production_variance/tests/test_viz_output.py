# -*- coding: utf-8 -*-
"""
C-25: 可視化出力テスト（4テスト以上）
"""
import pytest
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"

EXPECTED_CHARTS = [
    "bar_line_achievement.png",
    "bar_category_defect_rate.png",
    "scatter_planned_vs_actual.png",
]


# 1. charts ディレクトリ存在確認
def test_charts_dir_exists():
    assert CHARTS_DIR.exists(), f"chartsディレクトリが存在しません: {CHARTS_DIR}"


# 2. 棒グラフ（ライン別達成率）存在確認
def test_bar_line_achievement_exists():
    path = CHARTS_DIR / "bar_line_achievement.png"
    assert path.exists(), f"グラフが存在しません: {path}"


# 3. 棒グラフ（カテゴリ別不良率）存在確認
def test_bar_category_defect_rate_exists():
    path = CHARTS_DIR / "bar_category_defect_rate.png"
    assert path.exists(), f"グラフが存在しません: {path}"


# 4. 散布図（計画vs実績）存在確認
def test_scatter_planned_vs_actual_exists():
    path = CHARTS_DIR / "scatter_planned_vs_actual.png"
    assert path.exists(), f"グラフが存在しません: {path}"


# 5. 全グラフのファイルサイズ > 0
def test_all_charts_non_empty():
    for chart_name in EXPECTED_CHARTS:
        path = CHARTS_DIR / chart_name
        if path.exists():
            assert path.stat().st_size > 0, f"グラフファイルが空です: {path}"
        else:
            pytest.skip(f"グラフが存在しないためスキップ: {chart_name}")

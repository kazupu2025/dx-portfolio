# -*- coding: utf-8 -*-
"""
C-37: 来客記録データ集計・スループット分析パイプライン
可視化出力テスト (4 テスト以上)
"""

import pytest
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CHARTS_DIR = BASE_DIR / "output" / "charts"

EXPECTED_CHARTS = [
    "bar_dept_wait.png",
    "heatmap_timeslot_dept.png",
    "bar_wait_level.png",
]


# 1. charts ディレクトリが存在する
def test_charts_dir_exists():
    assert CHARTS_DIR.exists(), f"charts ディレクトリが存在しません: {CHARTS_DIR}"


# 2. 3 グラフすべてが存在する
def test_all_charts_exist():
    missing = [c for c in EXPECTED_CHARTS if not (CHARTS_DIR / c).exists()]
    assert not missing, f"グラフが存在しません: {missing}"


# 3. 各グラフのファイルサイズ > 0
@pytest.mark.parametrize("chart_name", EXPECTED_CHARTS)
def test_chart_file_size_positive(chart_name):
    path = CHARTS_DIR / chart_name
    if not path.exists():
        pytest.skip(f"{chart_name} が存在しません")
    size = path.stat().st_size
    assert size > 0, f"{chart_name} のファイルサイズが 0 バイト"


# 4. 各グラフのファイルサイズが十分（10KB 以上）
@pytest.mark.parametrize("chart_name", EXPECTED_CHARTS)
def test_chart_file_size_sufficient(chart_name):
    path = CHARTS_DIR / chart_name
    if not path.exists():
        pytest.skip(f"{chart_name} が存在しません")
    size = path.stat().st_size
    assert size >= 10_000, f"{chart_name} のファイルサイズが小さすぎます: {size} bytes"

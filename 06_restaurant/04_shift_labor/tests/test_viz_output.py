# -*- coding: utf-8 -*-
"""
C-40: 可視化出力テスト（4テスト以上）
"""

import pytest
from pathlib import Path

CHARTS_DIR = Path(__file__).parent.parent / "output" / "charts"


# 1. charts ディレクトリが存在すること
def test_charts_dir_exists():
    assert CHARTS_DIR.exists(), f"charts ディレクトリが存在しません: {CHARTS_DIR}"


# 2. 店舗別人件費グラフが存在すること
def test_store_labor_cost_chart_exists():
    chart = CHARTS_DIR / "bar_store_labor_cost.png"
    assert chart.exists(), f"グラフファイルが見つかりません: {chart}"


# 3. 役職別賃金グラフが存在すること
def test_role_avg_wage_chart_exists():
    chart = CHARTS_DIR / "bar_role_avg_wage.png"
    assert chart.exists(), f"グラフファイルが見つかりません: {chart}"


# 4. スタッフ別労働時間グラフが存在すること
def test_staff_hours_chart_exists():
    chart = CHARTS_DIR / "bar_staff_hours_top10.png"
    assert chart.exists(), f"グラフファイルが見つかりません: {chart}"


# 5. グラフファイルサイズが0バイト超
def test_chart_files_not_empty():
    for fname in [
        "bar_store_labor_cost.png",
        "bar_role_avg_wage.png",
        "bar_staff_hours_top10.png",
    ]:
        path = CHARTS_DIR / fname
        if path.exists():
            assert path.stat().st_size > 0, f"グラフファイルが空です: {fname}"

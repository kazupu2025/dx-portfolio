# -*- coding: utf-8 -*-
"""
C-52: test_viz_output.py
output/charts/ 以下のグラフ出力を検証する (3テスト以上)。
"""
import pytest
from pathlib import Path

CHARTS_DIR = Path("output/charts")


# 1. bar_type_count.png が存在する
def test_bar_type_count_exists():
    p = CHARTS_DIR / "bar_type_count.png"
    assert p.exists(), f"Graph not found: {p}"


# 2. bar_channel_satisfaction.png が存在する
def test_bar_channel_satisfaction_exists():
    p = CHARTS_DIR / "bar_channel_satisfaction.png"
    assert p.exists(), f"Graph not found: {p}"


# 3. bar_type_resolution.png が存在する
def test_bar_type_resolution_exists():
    p = CHARTS_DIR / "bar_type_resolution.png"
    assert p.exists(), f"Graph not found: {p}"


# 4. グラフのファイルサイズが 0 より大きい
def test_charts_not_empty():
    for fname in ["bar_type_count.png", "bar_channel_satisfaction.png", "bar_type_resolution.png"]:
        p = CHARTS_DIR / fname
        if p.exists():
            assert p.stat().st_size > 0, f"Graph file is empty: {fname}"

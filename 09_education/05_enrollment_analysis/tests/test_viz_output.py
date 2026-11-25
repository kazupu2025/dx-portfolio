# -*- coding: utf-8 -*-
"""
C-55 生徒入学申込・入学率分析パイプライン
可視化出力のpytestテスト（3テスト以上）
"""

import os
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS_DIR = os.path.join(BASE_DIR, "output", "charts")


# Test 1: 学科別合格率グラフが存在する
def test_bar_dept_enrollment_exists():
    path = os.path.join(CHARTS_DIR, "bar_dept_enrollment.png")
    assert os.path.exists(path), f"bar_dept_enrollment.png が存在しない: {path}"


# Test 2: 選考方法別合格率グラフが存在する
def test_bar_method_enrollment_exists():
    path = os.path.join(CHARTS_DIR, "bar_method_enrollment.png")
    assert os.path.exists(path), f"bar_method_enrollment.png が存在しない: {path}"


# Test 3: 地域別申込数グラフが存在する
def test_bar_region_count_exists():
    path = os.path.join(CHARTS_DIR, "bar_region_count.png")
    assert os.path.exists(path), f"bar_region_count.png が存在しない: {path}"


# Test 4: グラフのファイルサイズが0より大きい（正常に生成されている）
def test_chart_files_not_empty():
    chart_files = [
        "bar_dept_enrollment.png",
        "bar_method_enrollment.png",
        "bar_region_count.png",
    ]
    for fname in chart_files:
        path = os.path.join(CHARTS_DIR, fname)
        if os.path.exists(path):
            assert os.path.getsize(path) > 0, f"{fname} のファイルサイズが0"

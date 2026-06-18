# -*- coding: utf-8 -*-
"""
C-60 IT/SaaS - カスタマーサポートチケット分析
可視化出力テスト (3テスト以上)
"""

import os
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CHARTS_DIR = os.path.join(BASE_DIR, "output", "charts")

EXPECTED_CHARTS = [
    "bar_category_count.png",
    "bar_priority_escalation.png",
    "bar_agent_resolution.png",
]


def test_category_count_chart_exists():
    """bar_category_count.pngが存在する"""
    path = os.path.join(CHARTS_DIR, "bar_category_count.png")
    assert os.path.exists(path), f"グラフが見つかりません: {path}"


def test_priority_escalation_chart_exists():
    """bar_priority_escalation.pngが存在する"""
    path = os.path.join(CHARTS_DIR, "bar_priority_escalation.png")
    assert os.path.exists(path), f"グラフが見つかりません: {path}"


def test_agent_resolution_chart_exists():
    """bar_agent_resolution.pngが存在する"""
    path = os.path.join(CHARTS_DIR, "bar_agent_resolution.png")
    assert os.path.exists(path), f"グラフが見つかりません: {path}"


def test_chart_files_not_empty():
    """グラフファイルのサイズが0より大きい"""
    for fname in EXPECTED_CHARTS:
        path = os.path.join(CHARTS_DIR, fname)
        if os.path.exists(path):
            size = os.path.getsize(path)
            assert size > 0, f"グラフファイルが空: {path}"

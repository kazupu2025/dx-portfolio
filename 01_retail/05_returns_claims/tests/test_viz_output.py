# -*- coding: utf-8 -*-
"""
test_viz_output.py

visualize.py の出力グラフファイルを検証するテスト群。
pytest で実行: pytest tests/test_viz_output.py -v
"""

import pytest
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CHARTS_DIR = BASE_DIR / "output" / "charts"

EXPECTED_CHARTS = [
    "bar_store_claim_count.png",
    "bar_claim_type.png",
    "pie_response_level.png",
]


# ---- チャートディレクトリテスト ------------------------------------------

def test_charts_directory_exists():
    """output/charts/ ディレクトリが存在する。"""
    assert CHARTS_DIR.exists(), f"chartsディレクトリが存在しません: {CHARTS_DIR}"


# ---- 個別グラフテスト ----------------------------------------------------

@pytest.mark.parametrize("chart_name", EXPECTED_CHARTS)
def test_chart_file_exists(chart_name: str):
    """各グラフファイルが存在する。"""
    chart_path = CHARTS_DIR / chart_name
    assert chart_path.exists(), f"グラフが見つかりません: {chart_path}"


@pytest.mark.parametrize("chart_name", EXPECTED_CHARTS)
def test_chart_file_size(chart_name: str):
    """グラフファイルが空でない（1KB 以上）。"""
    chart_path = CHARTS_DIR / chart_name
    if not chart_path.exists():
        pytest.skip(f"ファイルが存在しません: {chart_path}")
    size_bytes = chart_path.stat().st_size
    assert size_bytes >= 1024, f"{chart_name} のサイズが小さすぎます: {size_bytes} bytes"


@pytest.mark.parametrize("chart_name", EXPECTED_CHARTS)
def test_chart_is_png(chart_name: str):
    """ファイルが PNG シグネチャを持つ。"""
    chart_path = CHARTS_DIR / chart_name
    if not chart_path.exists():
        pytest.skip(f"ファイルが存在しません: {chart_path}")
    # PNG ファイルは先頭 8 バイトが固定シグネチャ
    PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
    with open(chart_path, "rb") as f:
        header = f.read(8)
    assert header == PNG_SIGNATURE, f"{chart_name} は正しい PNG ではありません"

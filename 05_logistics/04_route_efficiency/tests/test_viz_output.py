# -*- coding: utf-8 -*-
"""
可視化出力ファイルのテスト (4テスト以上)
"""
import pytest
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CHARTS_DIR = BASE_DIR / "output" / "charts"

EXPECTED_CHARTS = [
    "bar_route_cost_per_delivery.png",
    "bar_area_delay_rate.png",
    "scatter_distance_cost.png",
]


def test_charts_dir_exists():
    """output/charts/ ディレクトリが存在する"""
    assert CHARTS_DIR.exists(), f"chartsディレクトリが見つかりません: {CHARTS_DIR}"


def test_all_chart_files_exist():
    """3つのグラフファイルがすべて存在する"""
    if not CHARTS_DIR.exists():
        pytest.skip("chartsディレクトリが存在しません")
    missing = [f for f in EXPECTED_CHARTS if not (CHARTS_DIR / f).exists()]
    assert missing == [], f"グラフファイルが見つかりません: {missing}"


def test_chart_files_not_empty():
    """グラフファイルのサイズが 0 より大きい"""
    if not CHARTS_DIR.exists():
        pytest.skip("chartsディレクトリが存在しません")
    for fname in EXPECTED_CHARTS:
        fpath = CHARTS_DIR / fname
        if fpath.exists():
            assert fpath.stat().st_size > 0, f"グラフファイルが空: {fname}"


def test_chart_files_are_png():
    """グラフファイルが PNG 形式である（ファイルシグネチャ確認）"""
    if not CHARTS_DIR.exists():
        pytest.skip("chartsディレクトリが存在しません")
    PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
    for fname in EXPECTED_CHARTS:
        fpath = CHARTS_DIR / fname
        if fpath.exists():
            with open(fpath, "rb") as f:
                header = f.read(8)
            assert header == PNG_SIGNATURE, f"PNG シグネチャが不一致: {fname}"

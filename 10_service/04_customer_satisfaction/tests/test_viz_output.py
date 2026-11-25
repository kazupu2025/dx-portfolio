# tests/test_viz_output.py — 可視化出力のテスト（C-36 顧客満足度）
# encoding: utf-8

import pytest
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"

EXPECTED_CHARTS = [
    "bar_service_csat.png",
    "bar_nps_category.png",
    "bar_agent_satisfaction.png",
]


# 1. charts ディレクトリが存在する
def test_charts_dir_exists():
    assert CHARTS_DIR.exists(), f"Charts directory not found: {CHARTS_DIR}"


# 2. bar_service_csat.png が存在する
def test_bar_service_csat_exists():
    path = CHARTS_DIR / "bar_service_csat.png"
    assert path.exists(), f"Chart not found: {path}"


# 3. bar_nps_category.png が存在する
def test_bar_nps_category_exists():
    path = CHARTS_DIR / "bar_nps_category.png"
    assert path.exists(), f"Chart not found: {path}"


# 4. bar_agent_satisfaction.png が存在する
def test_bar_agent_satisfaction_exists():
    path = CHARTS_DIR / "bar_agent_satisfaction.png"
    assert path.exists(), f"Chart not found: {path}"


# 5. 各グラフファイルのサイズが 10KB 以上（空でないことの確認）
@pytest.mark.parametrize("chart_name", EXPECTED_CHARTS)
def test_chart_file_size(chart_name):
    path = CHARTS_DIR / chart_name
    if not path.exists():
        pytest.skip(f"Chart not generated yet: {chart_name}")
    size_bytes = path.stat().st_size
    assert size_bytes >= 10_000, f"{chart_name} too small: {size_bytes} bytes (expected >= 10KB)"

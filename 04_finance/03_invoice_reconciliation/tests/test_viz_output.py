"""
C-26: test_viz_output.py
output/charts/ の可視化グラフを検証する (4テスト以上)。
"""
import pytest
from pathlib import Path

CHARTS_DIR = Path("output/charts")
EXPECTED_FILES = [
    "bar_match_status.png",
    "bar_client_variance_top10.png",
    "pie_payment_type.png",
]


# 1. charts ディレクトリが存在する
def test_charts_dir_exists():
    assert CHARTS_DIR.exists(), f"charts ディレクトリが存在しません: {CHARTS_DIR}"


# 2. bar_match_status.png が存在する
def test_bar_match_status_exists():
    p = CHARTS_DIR / "bar_match_status.png"
    assert p.exists(), f"グラフが存在しません: {p}"


# 3. bar_client_variance_top10.png が存在する
def test_bar_client_variance_exists():
    p = CHARTS_DIR / "bar_client_variance_top10.png"
    assert p.exists(), f"グラフが存在しません: {p}"


# 4. pie_payment_type.png が存在する
def test_pie_payment_type_exists():
    p = CHARTS_DIR / "pie_payment_type.png"
    assert p.exists(), f"グラフが存在しません: {p}"


# 5. 全グラフのファイルサイズが > 0
def test_all_charts_nonempty():
    for fname in EXPECTED_FILES:
        p = CHARTS_DIR / fname
        if p.exists():
            assert p.stat().st_size > 0, f"グラフが空です: {fname}"

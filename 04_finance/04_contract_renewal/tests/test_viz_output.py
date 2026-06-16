"""
C-31: test_viz_output.py
output/charts/ 内のグラフファイルを検証する (4テスト以上)。
"""
import pytest
from pathlib import Path

CHARTS_DIR = Path("output/charts")
EXPECTED_FILES = [
    "bar_renewal_status.png",
    "bar_agent_alert.png",
    "pie_insurance_type.png",
]


# 1. charts ディレクトリが存在する
def test_charts_dir_exists():
    assert CHARTS_DIR.exists(), f"charts ディレクトリが存在しません: {CHARTS_DIR}"


# 2. bar_renewal_status.png が存在する
def test_bar_renewal_status_exists():
    p = CHARTS_DIR / "bar_renewal_status.png"
    assert p.exists(), f"ファイルが存在しません: {p}"


# 3. bar_agent_alert.png が存在する
def test_bar_agent_alert_exists():
    p = CHARTS_DIR / "bar_agent_alert.png"
    assert p.exists(), f"ファイルが存在しません: {p}"


# 4. pie_insurance_type.png が存在する
def test_pie_insurance_type_exists():
    p = CHARTS_DIR / "pie_insurance_type.png"
    assert p.exists(), f"ファイルが存在しません: {p}"


# 5. 全グラフファイルのサイズが 0 より大きい
def test_all_charts_nonempty():
    for fname in EXPECTED_FILES:
        p = CHARTS_DIR / fname
        if p.exists():
            assert p.stat().st_size > 0, f"ファイルサイズが 0 です: {p}"

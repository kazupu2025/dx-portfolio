"""
C-21: 可視化出力テスト
charts/ 各PNGの存在確認
"""
import pytest
from pathlib import Path

BASE = Path(__file__).parent.parent
CHARTS_DIR = BASE / "output" / "charts"


def test_charts_dir_exists():
    assert CHARTS_DIR.exists(), f"charts/ ディレクトリが存在しません: {CHARTS_DIR}"


def test_bar_service_margin_exists():
    p = CHARTS_DIR / "bar_service_margin.png"
    assert p.exists(), f"グラフが存在しません: {p}"


def test_bar_dept_revenue_exists():
    p = CHARTS_DIR / "bar_dept_revenue.png"
    assert p.exists(), f"グラフが存在しません: {p}"


def test_pie_service_revenue_exists():
    p = CHARTS_DIR / "pie_service_revenue_share.png"
    assert p.exists(), f"グラフが存在しません: {p}"


def test_charts_count():
    pngs = list(CHARTS_DIR.glob("*.png"))
    assert len(pngs) >= 3, f"charts/ のPNG枚数が3未満: {len(pngs)}"

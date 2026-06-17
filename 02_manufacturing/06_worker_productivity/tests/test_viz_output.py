"""可視化出力テスト (4テスト以上)"""
import pytest
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CHARTS_DIR = BASE_DIR / "output" / "charts"


def test_bar_worker_productivity_top10_exists():
    assert (CHARTS_DIR / "bar_worker_productivity_top10.png").exists(), \
        "bar_worker_productivity_top10.png が存在しない"


def test_bar_line_defect_rate_exists():
    assert (CHARTS_DIR / "bar_line_defect_rate.png").exists(), \
        "bar_line_defect_rate.png が存在しない"


def test_scatter_productivity_defect_exists():
    assert (CHARTS_DIR / "scatter_productivity_defect.png").exists(), \
        "scatter_productivity_defect.png が存在しない"


def test_charts_dir_exists():
    assert CHARTS_DIR.exists(), f"charts ディレクトリが存在しない: {CHARTS_DIR}"


def test_chart_files_count():
    png_files = list(CHARTS_DIR.glob("*.png"))
    assert len(png_files) >= 3, f"チャートファイル数不足: {len(png_files)}"

import pytest
from pathlib import Path

CHARTS = Path("output/charts")

def test_charts_dir_exists(): assert CHARTS.exists()
def test_bar_process_defect_exists(): assert (CHARTS / "bar_process_defect_rate.png").exists()
def test_line_daily_defect_exists(): assert (CHARTS / "line_daily_defect_trend.png").exists()
def test_heatmap_exists(): assert (CHARTS / "heatmap_process_product.png").exists()

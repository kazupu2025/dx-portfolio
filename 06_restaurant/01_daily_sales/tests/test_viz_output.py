import pytest
from pathlib import Path

CHARTS = Path("output/charts")

def test_charts_dir_exists():
    assert CHARTS.exists()

def test_bar_store_sales_exists():
    assert (CHARTS / "bar_store_sales.png").exists()

def test_line_daily_sales_exists():
    assert (CHARTS / "line_daily_sales.png").exists()

def test_bar_waste_loss_exists():
    assert (CHARTS / "bar_waste_loss.png").exists()

import pytest
from pathlib import Path

CHARTS = Path("output/charts")

def test_charts_dir_exists():
    assert CHARTS.exists()

def test_bar_warehouse_stock_exists():
    assert (CHARTS / "bar_warehouse_stock.png").exists()

def test_bar_stockout_items_exists():
    assert (CHARTS / "bar_stockout_items.png").exists()

def test_scatter_turnover_exists():
    assert (CHARTS / "scatter_turnover.png").exists()

import pytest
from pathlib import Path

CHARTS = Path("output/charts")


def test_charts_dir_exists(): assert CHARTS.exists()

def test_bar_category_forecast(): assert (CHARTS / "bar_category_forecast.png").exists()

def test_bar_stockout_risk(): assert (CHARTS / "bar_stockout_risk.png").exists()

def test_scatter_stock_forecast(): assert (CHARTS / "scatter_stock_forecast.png").exists()

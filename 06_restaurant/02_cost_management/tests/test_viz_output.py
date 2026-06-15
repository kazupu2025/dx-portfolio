import pytest
from pathlib import Path

CHARTS = Path("output/charts")


def test_charts_dir_exists():
    assert CHARTS.exists()


def test_bar_category_cost_exists():
    assert (CHARTS / "bar_category_cost.png").exists()


def test_bar_store_loss_rate_exists():
    assert (CHARTS / "bar_store_loss_rate.png").exists()


def test_bar_ingredient_waste_exists():
    assert (CHARTS / "bar_ingredient_waste.png").exists()

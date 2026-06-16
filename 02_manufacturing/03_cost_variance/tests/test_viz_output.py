import pytest
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CHARTS_DIR = BASE_DIR / "output" / "charts"

def test_bar_line_variance_exists():
    assert (CHARTS_DIR / "bar_line_variance.png").exists()

def test_bar_product_variance_ratio_exists():
    assert (CHARTS_DIR / "bar_product_variance_ratio.png").exists()

def test_pie_variance_components_exists():
    assert (CHARTS_DIR / "pie_variance_components.png").exists()

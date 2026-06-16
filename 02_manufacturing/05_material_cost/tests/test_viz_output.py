import pytest
from pathlib import Path

CHARTS = Path("output/charts")


def test_charts_dir_exists():
    assert CHARTS.exists(), "output/charts ディレクトリが存在しない"


def test_bar_category_cost_exists():
    p = CHARTS / "bar_category_cost.png"
    assert p.exists(), "bar_category_cost.png が存在しない"


def test_bar_material_price_change_exists():
    p = CHARTS / "bar_material_price_change.png"
    assert p.exists(), "bar_material_price_change.png が存在しない"


def test_pie_supplier_cost_exists():
    p = CHARTS / "pie_supplier_cost.png"
    assert p.exists(), "pie_supplier_cost.png が存在しない"


def test_charts_file_sizes():
    for name in ["bar_category_cost.png", "bar_material_price_change.png", "pie_supplier_cost.png"]:
        p = CHARTS / name
        if p.exists():
            assert p.stat().st_size > 0, f"{name} のファイルサイズが 0"

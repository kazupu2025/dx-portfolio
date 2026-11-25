import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze, REQUIRED_COLUMNS


def make_df(avg_cost_per_ha=40000, n_months=6):
    """Create a sample DataFrame for testing."""
    crops = ["トマト", "キャベツ", "ほうれん草", "じゃがいも"]
    categories = ["殺虫剤", "殺菌剤", "除草剤", "窒素肥料", "リン酸肥料", "カリ肥料"]
    rows = []
    rng = np.random.default_rng(42)

    for m in range(n_months):
        for crop in crops:
            category = categories[rng.integers(0, len(categories))]
            field_area_ha = 1.5 + rng.normal(0, 0.2)

            # Calculate total_cost to achieve desired avg_cost_per_ha
            # With small variation
            target_cost = avg_cost_per_ha * field_area_ha
            total_cost = int(target_cost * (1 + rng.normal(0, 0.15)))
            total_cost = max(1000, total_cost)

            quantity_kg = 30 + rng.normal(0, 8)
            unit_price = total_cost / max(1, quantity_kg)

            rows.append(
                {
                    "date": f"2024-{m+1:02d}-15",
                    "crop": crop,
                    "product_name": f"Product_{category}_{rng.integers(1, 10)}",
                    "category": category,
                    "quantity_kg": max(1, quantity_kg),
                    "unit_price": max(100, unit_price),
                    "total_cost": total_cost,
                    "field_area_ha": field_area_ha,
                    "application_reason": ["病害虫対策", "予防", "定期施肥", "生育促進"][
                        rng.integers(0, 4)
                    ],
                }
            )
    return pd.DataFrame(rows)


def test_returns_dict():
    """Test that analyze returns a dictionary."""
    assert isinstance(analyze(make_df()), dict)


def test_required_keys():
    """Test that analyze result contains all required keys."""
    r = analyze(make_df())
    for k in [
        "df",
        "category_df",
        "crop_df",
        "monthly_df",
        "total_cost",
        "cost_per_ha",
        "category_count",
        "verdict",
    ]:
        assert k in r


def test_verdict_good():
    """Test verdict is 'good' when cost_per_ha <= 50000."""
    assert analyze(make_df(avg_cost_per_ha=40000))["verdict"] == "good"


def test_verdict_warning():
    """Test verdict is 'warning' when 50000 < cost_per_ha <= 80000."""
    assert analyze(make_df(avg_cost_per_ha=65000))["verdict"] == "warning"


def test_verdict_alert():
    """Test verdict is 'alert' when cost_per_ha > 80000."""
    assert analyze(make_df(avg_cost_per_ha=90000))["verdict"] == "alert"


def test_total_cost_positive():
    """Test that total_cost is positive."""
    assert analyze(make_df())["total_cost"] > 0


def test_crop_df_length():
    """Test that crop_df has exactly 4 crops."""
    assert len(analyze(make_df())["crop_df"]) == 4


def test_category_df_not_empty():
    """Test that category_df is not empty."""
    assert len(analyze(make_df())["category_df"]) > 0


def test_cost_per_ha_positive():
    """Test that cost_per_ha is positive."""
    assert analyze(make_df())["cost_per_ha"] > 0

import pandas as pd
import pytest
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CSV_PATH = BASE_DIR / "output" / "cleaned_production_cost_202401.csv"

def test_csv_exists():
    assert CSV_PATH.exists()

def test_row_count():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    assert len(df) >= 380

def test_required_columns():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    required = ["product_id","product_name","production_date","line_id",
                "planned_qty","actual_qty","planned_material","actual_material",
                "planned_labor","actual_labor","planned_overhead","actual_overhead",
                "source_file","material_variance","labor_variance","overhead_variance",
                "planned_total_cost","actual_total_cost","total_variance",
                "variance_ratio","qty_variance","variance_flag"]
    for col in required:
        assert col in df.columns, f"列が存在しない: {col}"

def test_variance_calculation():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    calc = df["actual_total_cost"] - df["planned_total_cost"]
    assert (calc - df["total_variance"]).abs().max() < 1

def test_variance_flag_values():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    assert set(df["variance_flag"].unique()).issubset({"超過","節約","正常"})

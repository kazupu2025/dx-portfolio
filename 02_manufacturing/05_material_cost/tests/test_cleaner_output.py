import pandas as pd
import pytest
from pathlib import Path

CSV = Path("output/cleaned_material_202401.csv")


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(CSV, encoding="utf-8-sig")


def test_csv_exists():
    assert CSV.exists(), "cleaned_material_202401.csv が存在しない"


def test_row_count(df):
    assert len(df) >= 400, f"行数 {len(df)} < 400"


def test_required_columns(df):
    required = {
        "purchase_date", "material_code", "material_name", "category",
        "supplier", "quantity", "unit_price", "prev_month_price",
        "price_change_rate", "total_cost", "price_change_flag", "source_file",
    }
    missing = required - set(df.columns)
    assert len(missing) == 0, f"必須列が不足: {missing}"


def test_date_format(df):
    import re
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    bad = df["purchase_date"].dropna()[~df["purchase_date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")]
    assert len(bad) == 0, f"不正日付 {len(bad)} 件"


def test_material_code_variety(df):
    n = df["material_code"].nunique()
    assert n >= 10, f"material_code の種類 {n} < 10"


def test_category_count(df):
    n = df["category"].nunique()
    assert n == 4, f"category の種類 {n} (期待: 4)"


def test_supplier_count(df):
    n = df["supplier"].nunique()
    assert n == 5, f"supplier の種類 {n} (期待: 5)"


def test_unit_price_positive(df):
    n_bad = (df["unit_price"] <= 0).sum()
    assert n_bad == 0, f"unit_price <= 0 が {n_bad} 件"


def test_price_change_flag_values(df):
    valid = {"急騰", "急落", "安定"}
    actual = set(df["price_change_flag"].dropna().unique())
    invalid = actual - valid
    assert len(invalid) == 0, f"不正フラグ: {invalid}"


def test_source_file_column(df):
    assert "source_file" in df.columns, "source_file 列がない"


def test_source_file_count(df):
    n = df["source_file"].nunique()
    assert n == 3, f"source_file の種類 {n} (期待: 3)"


def test_total_cost_consistency(df):
    expected = (df["quantity"] * df["unit_price"]).round(0)
    diff = (df["total_cost"] - expected).abs()
    n_mismatch = (diff > 1).sum()
    assert n_mismatch == 0, f"total_cost 不整合 {n_mismatch} 件"


def test_has_soar_records(df):
    n = (df["price_change_flag"] == "急騰").sum()
    assert n >= 1, f"急騰件数 {n} < 1"


def test_has_drop_records(df):
    n = (df["price_change_flag"] == "急落").sum()
    assert n >= 1, f"急落件数 {n} < 1"

# -*- coding: utf-8 -*-
"""
C-29: 薬品在庫管理・発注アラートパイプライン
クレンジング出力テスト (10 テスト以上)
"""

import re
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
CSV_PATH = OUTPUT_DIR / "cleaned_medicine_202401.csv"

REQUIRED_COLS = [
    "date", "med_code", "med_name", "category", "ward",
    "stock_qty", "min_stock", "daily_usage", "unit_price",
    "source_file", "days_until_stockout", "stock_value", "alert_level",
]


@pytest.fixture(scope="module")
def df():
    assert CSV_PATH.exists(), f"CSVが存在しません: {CSV_PATH}"
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


# 1. ファイル存在確認
def test_csv_exists():
    assert CSV_PATH.exists(), f"cleaned_medicine_202401.csv が存在しません: {CSV_PATH}"


# 2. 行数 >= 400
def test_row_count(df):
    assert len(df) >= 400, f"行数が不足: {len(df)} 件 (期待: >= 400)"


# 3. 必須列の存在
def test_required_columns(df):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    assert not missing, f"不足列: {missing}"


# 4. 日付フォーマット YYYY-MM-DD
def test_date_format(df):
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    bad = df["date"].dropna()[~df["date"].dropna().apply(lambda x: bool(pattern.match(str(x))))]
    assert len(bad) == 0, f"日付フォーマット不正: {len(bad)} 件"


# 5. med_code が 30 種類以上
def test_med_code_variety(df):
    n = df["med_code"].nunique()
    assert n >= 30, f"med_code の種類が不足: {n} 種類 (期待: >= 30)"


# 6. category が 5 種類
def test_category_count(df):
    n = df["category"].nunique()
    assert n == 5, f"category が {n} 種類 (期待: 5)"


# 7. ward が 4 種類
def test_ward_count(df):
    n = df["ward"].nunique()
    assert n == 4, f"ward が {n} 種類 (期待: 4)"


# 8. stock_qty が非負
def test_stock_qty_non_negative(df):
    bad = df["stock_qty"].dropna()[df["stock_qty"].dropna() < 0]
    assert len(bad) == 0, f"stock_qty に負値が {len(bad)} 件"


# 9. alert_level の値域
def test_alert_level_values(df):
    valid = {"欠品", "警告", "正常"}
    bad = df["alert_level"].dropna()[~df["alert_level"].dropna().isin(valid)]
    assert len(bad) == 0, f"alert_level に不正値が {len(bad)} 件: {bad.unique()}"


# 10. source_file 列の存在
def test_source_file_column(df):
    assert "source_file" in df.columns, "source_file 列が存在しません"


# 11. source_file が 3 種類
def test_source_file_variety(df):
    n = df["source_file"].nunique()
    assert n == 3, f"source_file が {n} 種類 (期待: 3)"


# 12. min_stock が正値
def test_min_stock_positive(df):
    bad = df["min_stock"].dropna()[df["min_stock"].dropna() <= 0]
    assert len(bad) == 0, f"min_stock に 0 以下の値が {len(bad)} 件"


# 13. days_until_stockout が非負または NaN
def test_days_until_stockout_non_negative(df):
    ds = df["days_until_stockout"].dropna()
    bad = ds[ds < 0]
    assert len(bad) == 0, f"days_until_stockout に負値が {len(bad)} 件"


# 14. 欠品件数 >= 1
def test_shortage_exists(df):
    n = (df["alert_level"] == "欠品").sum()
    assert n >= 1, "欠品レコードが 0 件"

# -*- coding: utf-8 -*-
"""
C-54: クレンジング出力テスト（10テスト以上）
"""

import pytest
import pandas as pd
from pathlib import Path

OUTPUT_FILE = Path(__file__).parent.parent / "output" / "cleaned_pl_202401.csv"

REQUIRED_COLS = [
    "record_date", "record_id", "store_name", "revenue",
    "food_cost", "labor_cost", "other_cost",
    "total_cost", "gross_profit",
    "food_cost_rate", "labor_cost_rate", "profit_margin",
    "pl_flag", "source_file",
]

STORES_EXPECTED = {"渋谷店", "新宿店", "池袋店", "銀座店", "品川店"}


@pytest.fixture(scope="module")
def df():
    assert OUTPUT_FILE.exists(), f"クレンジングファイルが存在しません: {OUTPUT_FILE}"
    return pd.read_csv(OUTPUT_FILE, encoding="utf-8-sig")


# 1. ファイルが存在すること
def test_output_file_exists():
    assert OUTPUT_FILE.exists(), f"ファイルが見つかりません: {OUTPUT_FILE}"


# 2. 行数が420以上
def test_row_count(df):
    assert len(df) >= 420, f"行数が不足: {len(df)}"


# 3. 必須列が全て存在
def test_required_columns(df):
    for col in REQUIRED_COLS:
        assert col in df.columns, f"列が存在しない: {col}"


# 4. 日付フォーマットが YYYY-MM-DD
def test_date_format(df):
    pattern = df["record_date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")
    assert pattern.all(), f"不正な日付フォーマット: {df.loc[~pattern, 'record_date'].head().tolist()}"


# 5. record_id が一意
def test_record_id_unique(df):
    assert df["record_id"].nunique() == len(df), f"record_id に重複あり"


# 6. store_name が5種類
def test_store_name_count(df):
    stores = set(df["store_name"].unique())
    assert stores == STORES_EXPECTED, f"store_name の種類が不正: {stores}"


# 7. revenue が全て正の値
def test_revenue_positive(df):
    vals = pd.to_numeric(df["revenue"], errors="coerce")
    assert (vals > 0).all(), "revenue に 0 以下の値が存在"


# 8. food_cost >= 0
def test_food_cost_non_negative(df):
    vals = pd.to_numeric(df["food_cost"], errors="coerce")
    assert (vals >= 0).all(), "food_cost に負の値が存在"


# 9. labor_cost >= 0
def test_labor_cost_non_negative(df):
    vals = pd.to_numeric(df["labor_cost"], errors="coerce")
    assert (vals >= 0).all(), "labor_cost に負の値が存在"


# 10. other_cost >= 0
def test_other_cost_non_negative(df):
    vals = pd.to_numeric(df["other_cost"], errors="coerce")
    assert (vals >= 0).all(), "other_cost に負の値が存在"


# 11. total_cost > 0
def test_total_cost_positive(df):
    vals = pd.to_numeric(df["total_cost"], errors="coerce")
    assert (vals > 0).all(), "total_cost に 0 以下の値が存在"


# 12. gross_profit 計算整合性
def test_gross_profit_consistency(df):
    rev = pd.to_numeric(df["revenue"], errors="coerce")
    tc = pd.to_numeric(df["total_cost"], errors="coerce")
    gp = pd.to_numeric(df["gross_profit"], errors="coerce")
    diff = (gp - (rev - tc)).abs()
    assert (diff < 1).all(), f"gross_profit の計算が不整合: 最大誤差={diff.max()}"


# 13. food_cost_rate が [0, 1] の範囲
def test_food_cost_rate_range(df):
    vals = pd.to_numeric(df["food_cost_rate"], errors="coerce").dropna()
    assert ((vals >= 0) & (vals <= 1)).all(), "food_cost_rate に範囲外の値が存在"


# 14. pl_flag が 黒字/赤字 のみ
def test_pl_flag_values(df):
    unique_vals = set(df["pl_flag"].unique())
    assert unique_vals.issubset({"黒字", "赤字"}), f"pl_flag に不正な値: {unique_vals}"


# 15. source_file が 3 種類
def test_source_file_count(df):
    count = df["source_file"].nunique()
    assert count == 3, f"source_file の種類数が不正: {count}"


# 16. 欠損率が15%以下
def test_null_rate(df):
    total = df.shape[0] * df.shape[1]
    nulls = df.isnull().sum().sum()
    rate = nulls / total
    assert rate <= 0.15, f"欠損率が高すぎる: {rate:.2%}"

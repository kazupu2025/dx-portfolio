# -*- coding: utf-8 -*-
"""
C-40: クレンジング出力テスト（10テスト以上）
"""

import pytest
import pandas as pd
from pathlib import Path

OUTPUT_FILE = Path(__file__).parent.parent / "output" / "cleaned_shift_202401.csv"

REQUIRED_COLS = [
    "work_date", "staff_id", "store_name", "role",
    "start_time", "end_time", "work_hours", "hourly_rate",
    "daily_wage", "is_overtime", "labor_cost_flag", "source_file",
]


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
    pattern = df["work_date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")
    assert pattern.all(), f"不正な日付フォーマットが存在: {df.loc[~pattern, 'work_date'].head().tolist()}"


# 5. staff_id が10種類以上
def test_staff_id_variety(df):
    count = df["staff_id"].nunique()
    assert count >= 10, f"staff_id の種類数が不足: {count}"


# 6. store_name が3種類
def test_store_name_count(df):
    count = df["store_name"].nunique()
    assert count == 3, f"store_name の種類数が不正: {count}"


# 7. role が3種類
def test_role_count(df):
    count = df["role"].nunique()
    assert count == 3, f"role の種類数が不正: {count}"


# 8. work_hours が全て正の値
def test_work_hours_positive(df):
    vals = pd.to_numeric(df["work_hours"], errors="coerce")
    assert (vals > 0).all(), "work_hours に 0 以下の値が存在"


# 9. hourly_rate が800以上（最低賃金チェック）
def test_hourly_rate_minimum(df):
    vals = pd.to_numeric(df["hourly_rate"], errors="coerce")
    assert (vals >= 800).all(), f"hourly_rate が最低賃金以下の行が存在: {vals[vals < 800].values}"


# 10. daily_wage が正の値
def test_daily_wage_positive(df):
    vals = pd.to_numeric(df["daily_wage"], errors="coerce")
    assert (vals > 0).all(), "daily_wage に 0 以下の値が存在"


# 11. is_overtime が 0 または 1 のみ
def test_is_overtime_values(df):
    unique_vals = set(df["is_overtime"].unique())
    assert unique_vals.issubset({0, 1}), f"is_overtime に不正な値: {unique_vals}"


# 12. labor_cost_flag が "高コスト" または "標準" のみ
def test_labor_cost_flag_values(df):
    unique_vals = set(df["labor_cost_flag"].unique())
    assert unique_vals.issubset({"高コスト", "標準"}), f"labor_cost_flag に不正な値: {unique_vals}"


# 13. source_file 列が3種類
def test_source_file_count(df):
    count = df["source_file"].nunique()
    assert count == 3, f"source_file の種類数が不正: {count}"


# 14. 欠損率が15%以下
def test_null_rate(df):
    total = df.shape[0] * df.shape[1]
    nulls = df.isnull().sum().sum()
    rate = nulls / total
    assert rate <= 0.15, f"欠損率が高すぎる: {rate:.2%}"


# 15. 残業シフトが1件以上
def test_overtime_exists(df):
    count = int((df["is_overtime"] == 1).sum())
    assert count >= 1, "残業シフトが存在しない"

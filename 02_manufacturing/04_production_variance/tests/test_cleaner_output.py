# -*- coding: utf-8 -*-
"""
C-25: クレンジング出力テスト（10テスト以上）
"""
import re
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
CLEANED_CSV = OUTPUT_DIR / "cleaned_production_202401.csv"

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

REQUIRED_COLS = [
    "date", "line_name", "category",
    "planned_qty", "actual_qty", "defect_qty", "work_hours",
    "achievement_rate", "defect_rate", "variance_qty", "achievement_flag",
    "source_file",
]

EXPECTED_LINES = {"LINE-A", "LINE-B", "LINE-C", "LINE-D", "LINE-E"}
EXPECTED_CATEGORIES = {"電子部品", "機械部品", "樹脂成型", "金属加工"}


@pytest.fixture(scope="module")
def df():
    if not CLEANED_CSV.exists():
        pytest.skip(f"クレンジング済みCSVが見つかりません: {CLEANED_CSV}")
    return pd.read_csv(CLEANED_CSV, encoding="utf-8-sig")


# 1. CSV存在確認
def test_csv_exists():
    assert CLEANED_CSV.exists(), f"ファイルが存在しません: {CLEANED_CSV}"


# 2. 行数 >= 400
def test_row_count(df):
    assert len(df) >= 400, f"行数不足: {len(df)} < 400"


# 3. 必須列の存在（12列）
def test_required_columns(df):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    assert missing == [], f"必須列が不足: {missing}"


# 4. 日付フォーマット YYYY-MM-DD
def test_date_format(df):
    invalid = df["date"].dropna().apply(lambda x: not bool(DATE_PATTERN.match(str(x))))
    assert not invalid.any(), f"不正な日付フォーマットが {invalid.sum()} 件あります"


# 5. ライン種類（LINE-A〜LINE-E）
def test_line_names(df):
    actual = set(df["line_name"].dropna().unique())
    assert actual == EXPECTED_LINES, f"ライン種類不一致: actual={actual}"


# 6. カテゴリ種類（4種類）
def test_category_names(df):
    actual = set(df["category"].dropna().unique())
    assert actual == EXPECTED_CATEGORIES, f"カテゴリ種類不一致: actual={actual}"


# 7. planned_qty > 0
def test_planned_qty_positive(df):
    non_positive = (df["planned_qty"] <= 0).sum()
    assert non_positive == 0, f"planned_qty <= 0 が {non_positive} 件あります"


# 8. defect_rate が [0, 1] の範囲
def test_defect_rate_range(df):
    dr = df["defect_rate"].dropna()
    out_of_range = ((dr < 0) | (dr > 1)).sum()
    assert out_of_range == 0, f"defect_rate が [0,1] 外の値が {out_of_range} 件あります"


# 9. achievement_flag の値域
def test_achievement_flag_values(df):
    valid_flags = {"達成", "未達"}
    actual_flags = set(df["achievement_flag"].dropna().unique())
    assert actual_flags.issubset(valid_flags), f"不正なachievement_flag値: {actual_flags - valid_flags}"


# 10. source_file 列の存在
def test_source_file_column(df):
    assert "source_file" in df.columns, "source_file 列が存在しません"


# 11. source_file が 3 種類
def test_source_file_count(df):
    n_sources = df["source_file"].nunique()
    assert n_sources == 3, f"source_file の種類数: expected=3, actual={n_sources}"


# 12. variance_qty 整合性（actual_qty - planned_qty との差が 0.01 以下）
def test_variance_qty_consistency(df):
    diff = (df["variance_qty"] - (df["actual_qty"] - df["planned_qty"])).abs()
    violations = (diff > 0.01).sum()
    assert violations == 0, f"variance_qty の不整合が {violations} 件あります"


# 13. actual_qty >= 0
def test_actual_qty_non_negative(df):
    neg = (df["actual_qty"] < 0).sum()
    assert neg == 0, f"actual_qty < 0 が {neg} 件あります"


# 14. defect_qty <= actual_qty
def test_defect_qty_not_exceed_actual(df):
    violations = (df["defect_qty"] > df["actual_qty"]).sum()
    assert violations == 0, f"defect_qty > actual_qty が {violations} 件あります"

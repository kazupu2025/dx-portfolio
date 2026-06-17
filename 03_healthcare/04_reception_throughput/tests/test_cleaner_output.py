# -*- coding: utf-8 -*-
"""
C-37: 来客記録データ集計・スループット分析パイプライン
クレンジング出力テスト (10 テスト以上)
"""

import re
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
CSV_PATH = OUTPUT_DIR / "cleaned_reception_202401.csv"

REQUIRED_COLS = [
    "visit_date", "reception_no", "department",
    "arrival_time", "start_time", "end_time",
    "wait_minutes", "treat_minutes",
    "source_file", "wait_level", "time_slot",
]

VALID_DEPARTMENTS = {"内科", "外科", "整形外科", "小児科", "眼科"}
VALID_WAIT_LEVELS = {"長待ち", "普通", "短待ち"}


@pytest.fixture(scope="module")
def df():
    assert CSV_PATH.exists(), f"CSVが存在しません: {CSV_PATH}"
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


# 1. ファイル存在確認
def test_csv_exists():
    assert CSV_PATH.exists(), f"cleaned_reception_202401.csv が存在しません: {CSV_PATH}"


# 2. 行数 >= 420
def test_row_count(df):
    assert len(df) >= 420, f"行数が不足: {len(df)} 件 (期待: >= 420)"


# 3. 必須列の存在（11列）
def test_required_columns(df):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    assert not missing, f"不足列: {missing}"


# 4. reception_no のユニーク性
def test_reception_no_unique(df):
    n_total = len(df)
    n_unique = df["reception_no"].nunique()
    assert n_unique == n_total, f"reception_no に重複: {n_total - n_unique} 件"


# 5. 日付フォーマット YYYY-MM-DD
def test_date_format(df):
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    bad = df["visit_date"].dropna()[
        ~df["visit_date"].dropna().apply(lambda x: bool(pattern.match(str(x))))
    ]
    assert len(bad) == 0, f"日付フォーマット不正: {len(bad)} 件"


# 6. department が 5 種類
def test_department_count(df):
    depts = set(df["department"].dropna().unique())
    assert depts == VALID_DEPARTMENTS, f"diagnostics: {sorted(depts)}"


# 7. wait_minutes >= 0
def test_wait_minutes_non_negative(df):
    bad = df["wait_minutes"].dropna()[df["wait_minutes"].dropna() < 0]
    assert len(bad) == 0, f"wait_minutes に負値が {len(bad)} 件"


# 8. treat_minutes > 0
def test_treat_minutes_positive(df):
    bad = df["treat_minutes"].dropna()[df["treat_minutes"].dropna() <= 0]
    assert len(bad) == 0, f"treat_minutes に 0 以下の値が {len(bad)} 件"


# 9. wait_level の値域
def test_wait_level_values(df):
    bad = df["wait_level"].dropna()[~df["wait_level"].dropna().isin(VALID_WAIT_LEVELS)]
    assert len(bad) == 0, f"wait_level に不正値が {len(bad)} 件: {bad.unique()}"


# 10. time_slot が NULL ではない
def test_time_slot_not_null(df):
    null_count = df["time_slot"].isna().sum()
    assert null_count == 0, f"time_slot に NULL が {null_count} 件"


# 11. source_file 列の存在
def test_source_file_column(df):
    assert "source_file" in df.columns, "source_file 列が存在しません"


# 12. source_file が 3 種類
def test_source_file_variety(df):
    n = df["source_file"].nunique()
    assert n == 3, f"source_file が {n} 種類 (期待: 3)"


# 13. 長待ち件数 >= 1
def test_long_wait_exists(df):
    n = (df["wait_level"] == "長待ち").sum()
    assert n >= 1, "長待ちレコードが 0 件"


# 14. wait_minutes の最大値 <= 200
def test_wait_minutes_max(df):
    max_val = df["wait_minutes"].dropna().max()
    assert max_val <= 200, f"wait_minutes の最大値が {max_val} (期待: <= 200)"


# 15. treat_minutes の最大値 <= 120
def test_treat_minutes_max(df):
    max_val = df["treat_minutes"].dropna().max()
    assert max_val <= 120, f"treat_minutes の最大値が {max_val} (期待: <= 120)"

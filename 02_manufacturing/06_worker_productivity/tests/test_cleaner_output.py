"""クレンジング出力テスト (10テスト以上)"""
import re
import pandas as pd
import pytest
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CSV_PATH = BASE_DIR / "output" / "cleaned_worker_202401.csv"

REQUIRED_COLS = [
    "work_date", "worker_id", "line", "process",
    "production_qty", "defect_qty", "work_hours", "overtime_hours",
    "defect_rate", "productivity", "performance_flag", "source_file",
]


@pytest.fixture(scope="module")
def df():
    assert CSV_PATH.exists(), f"CSV not found: {CSV_PATH}"
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def test_csv_exists():
    assert CSV_PATH.exists()


def test_row_count(df):
    assert len(df) >= 400, f"行数不足: {len(df)}"


def test_required_columns(df):
    for col in REQUIRED_COLS:
        assert col in df.columns, f"列が存在しない: {col}"


def test_date_format(df):
    bad = df["work_date"].dropna().apply(
        lambda x: not bool(re.match(r"\d{4}-\d{2}-\d{2}", str(x)))
    )
    assert bad.sum() == 0, f"日付フォーマット不正: {bad.sum()}件"


def test_worker_id_variety(df):
    assert df["worker_id"].nunique() >= 20, f"作業員種類不足: {df['worker_id'].nunique()}"


def test_line_variety(df):
    assert df["line"].nunique() == 4, f"ライン数不正: {df['line'].nunique()}"


def test_process_variety(df):
    assert df["process"].nunique() == 4, f"工程数不正: {df['process'].nunique()}"


def test_production_qty_positive(df):
    assert (df["production_qty"] > 0).all(), "production_qty に0以下の値が存在する"


def test_defect_qty_non_negative(df):
    assert (df["defect_qty"] >= 0).all(), "defect_qty に負の値が存在する"


def test_defect_qty_le_production(df):
    assert (df["defect_qty"] <= df["production_qty"]).all(), \
        "defect_qty > production_qty の行が存在する"


def test_work_hours_positive(df):
    assert (df["work_hours"] > 0).all(), "work_hours に0以下の値が存在する"


def test_overtime_hours_non_negative(df):
    assert (df["overtime_hours"] >= 0).all(), "overtime_hours に負の値が存在する"


def test_defect_rate_range(df):
    valid = df["defect_rate"].dropna()
    assert ((valid >= 0) & (valid <= 1)).all(), "defect_rate が0~1の範囲外"


def test_productivity_positive(df):
    valid = df["productivity"].dropna()
    assert (valid > 0).all(), "productivity に0以下の値が存在する"


def test_performance_flag_values(df):
    valid_flags = {"高生産性", "低生産性"}
    actual = set(df["performance_flag"].dropna().unique())
    assert actual.issubset(valid_flags), f"無効なperformance_flag値: {actual - valid_flags}"


def test_source_file_variety(df):
    assert df["source_file"].nunique() == 3, \
        f"source_file の種類数不正: {df['source_file'].nunique()}"

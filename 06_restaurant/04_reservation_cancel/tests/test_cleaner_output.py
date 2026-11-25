# -*- coding: utf-8 -*-
"""
C-38: クレンジング出力テスト (10テスト以上)
"""

import pytest
import pandas as pd
from pathlib import Path

OUTPUT_FILE = Path(__file__).parent.parent / "output" / "cleaned_reservations_202401.csv"

REQUIRED_COLUMNS = [
    "reserv_date", "reserv_no", "store_name", "course",
    "guest_count", "amount", "status", "cancel_reason",
    "is_cancel", "loss_amount", "day_of_week", "source_file",
]

VALID_STATUSES = {"予約済み", "キャンセル", "来店済み"}
VALID_WEEKDAYS = {"月", "火", "水", "木", "金", "土", "日"}
EXPECTED_STORES = {"渋谷店", "新宿店", "銀座店"}
EXPECTED_COURSES = {"ランチ", "ディナー", "飲み放題", "個室コース"}


@pytest.fixture(scope="module")
def df():
    assert OUTPUT_FILE.exists(), f"Output file not found: {OUTPUT_FILE}"
    _df = pd.read_csv(OUTPUT_FILE, encoding="utf-8-sig", dtype=str)
    _df["guest_count_num"] = pd.to_numeric(_df["guest_count"], errors="coerce")
    _df["amount_num"] = pd.to_numeric(_df["amount"], errors="coerce")
    _df["is_cancel_num"] = pd.to_numeric(_df["is_cancel"], errors="coerce")
    _df["loss_amount_num"] = pd.to_numeric(_df["loss_amount"], errors="coerce")
    return _df


def test_01_file_exists():
    """クレンジング出力ファイルが存在する"""
    assert OUTPUT_FILE.exists(), f"File not found: {OUTPUT_FILE}"


def test_02_row_count(df):
    """行数が420以上である"""
    assert len(df) >= 420, f"Row count {len(df)} < 420"


def test_03_required_columns_exist(df):
    """必須列が全て存在する"""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    assert missing == [], f"Missing columns: {missing}"


def test_04_reserv_no_unique(df):
    """予約番号がユニークである"""
    dup_count = df["reserv_no"].duplicated().sum()
    assert dup_count == 0, f"Duplicate reserv_no count: {dup_count}"


def test_05_date_format(df):
    """日付が YYYY-MM-DD フォーマットである"""
    valid = df["reserv_date"].str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)
    invalid_count = (~valid).sum()
    assert invalid_count == 0, f"Invalid date format count: {invalid_count}"


def test_06_store_name_variety(df):
    """store_name が3種類ある"""
    stores = set(df["store_name"].dropna().unique())
    assert stores == EXPECTED_STORES, f"Stores found: {stores}"


def test_07_course_variety(df):
    """course が4種類ある"""
    courses = set(df["course"].dropna().unique())
    assert courses == EXPECTED_COURSES, f"Courses found: {courses}"


def test_08_guest_count_positive(df):
    """guest_count が全て1以上である"""
    invalid = (df["guest_count_num"] < 1).sum()
    assert invalid == 0, f"Rows with guest_count < 1: {invalid}"


def test_09_amount_non_negative(df):
    """amount が全て0以上である"""
    invalid = (df["amount_num"] < 0).sum()
    assert invalid == 0, f"Rows with amount < 0: {invalid}"


def test_10_status_valid_values(df):
    """status が有効値のみである"""
    invalid_mask = ~df["status"].isin(VALID_STATUSES)
    assert invalid_mask.sum() == 0, f"Invalid status values: {df.loc[invalid_mask, 'status'].unique()}"


def test_11_is_cancel_binary(df):
    """is_cancel が 0 または 1 のみである"""
    invalid = ~df["is_cancel_num"].isin([0, 1])
    assert invalid.sum() == 0, f"Invalid is_cancel values count: {invalid.sum()}"


def test_12_loss_amount_non_negative(df):
    """loss_amount が全て0以上である"""
    invalid = (df["loss_amount_num"] < 0).sum()
    assert invalid == 0, f"Rows with loss_amount < 0: {invalid}"


def test_13_loss_amount_consistent_with_is_cancel(df):
    """is_cancel=1 のとき loss_amount == amount, is_cancel=0 のとき loss_amount == 0"""
    cancel_rows = df[df["is_cancel_num"] == 1]
    mismatch_cancel = (cancel_rows["loss_amount_num"] != cancel_rows["amount_num"]).sum()
    assert mismatch_cancel == 0, f"Cancel rows where loss_amount != amount: {mismatch_cancel}"

    non_cancel_rows = df[df["is_cancel_num"] == 0]
    mismatch_non_cancel = (non_cancel_rows["loss_amount_num"] != 0).sum()
    assert mismatch_non_cancel == 0, f"Non-cancel rows where loss_amount != 0: {mismatch_non_cancel}"


def test_14_day_of_week_valid(df):
    """day_of_week が有効な曜日のみである"""
    invalid_mask = ~df["day_of_week"].isin(VALID_WEEKDAYS)
    assert invalid_mask.sum() == 0, f"Invalid weekday values: {df.loc[invalid_mask, 'day_of_week'].unique()}"


def test_15_source_file_column_exists(df):
    """source_file 列が存在し3種類ある"""
    assert "source_file" in df.columns
    n_src = df["source_file"].nunique()
    assert n_src == 3, f"Expected 3 source files, got {n_src}"


def test_16_cancel_reason_only_for_cancel(df):
    """cancel_reason はキャンセル行のみに値がある（非キャンセル行はNaN）"""
    non_cancel = df[df["is_cancel_num"] == 0]
    non_cancel_with_reason = non_cancel["cancel_reason"].dropna()
    # 空文字列も除外
    non_cancel_with_reason = non_cancel_with_reason[non_cancel_with_reason != ""]
    assert len(non_cancel_with_reason) == 0, (
        f"Non-cancel rows with cancel_reason: {len(non_cancel_with_reason)}"
    )

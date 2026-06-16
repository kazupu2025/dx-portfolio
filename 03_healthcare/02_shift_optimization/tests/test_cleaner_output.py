"""
test_cleaner_output.py
cleanse.py の出力 (cleaned_shift_202401.csv) をテストする。
"""

import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(BASE_DIR, "output", "cleaned_shift_202401.csv")

VALID_SHIFTS = {"早番", "日勤", "遅番", "夜勤", "休み"}


@pytest.fixture(scope="module")
def df():
    assert os.path.isfile(OUTPUT_FILE), f"ファイルが存在しません: {OUTPUT_FILE}"
    return pd.read_csv(OUTPUT_FILE, encoding="utf-8-sig")


def test_file_exists():
    assert os.path.isfile(OUTPUT_FILE)


def test_row_count(df):
    assert len(df) >= 450, f"行数が450未満: {len(df)}"


def test_required_columns(df):
    required = ["staff_id", "name", "role", "date", "preferred_shift", "skill_level", "employment_type"]
    for col in required:
        assert col in df.columns, f"列 '{col}' が存在しない"


def test_preferred_shift_values(df):
    invalid = df["preferred_shift"].dropna()[~df["preferred_shift"].dropna().isin(VALID_SHIFTS)]
    assert len(invalid) == 0, f"不正なシフト値: {invalid.unique().tolist()}"


def test_is_night_column(df):
    assert "is_night" in df.columns
    assert df["is_night"].dropna().isin([True, False]).all(), "is_night は True/False のみのはず"


def test_is_off_column(df):
    assert "is_off" in df.columns
    assert df["is_off"].dropna().isin([True, False]).all(), "is_off は True/False のみのはず"


def test_is_night_consistency(df):
    """is_night が preferred_shift == '夜勤' と一致する"""
    expected = df["preferred_shift"] == "夜勤"
    assert (df["is_night"] == expected).all()


def test_is_off_consistency(df):
    """is_off が preferred_shift == '休み' と一致する"""
    expected = df["preferred_shift"] == "休み"
    assert (df["is_off"] == expected).all()


def test_source_file_column(df):
    assert "source_file" in df.columns
    assert df["source_file"].notna().all()


def test_date_format(df):
    import re
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    bad = df["date"].dropna().apply(lambda v: not bool(pattern.match(str(v))))
    assert not bad.any(), f"日付フォーマット不正: {df['date'][bad].unique()[:5]}"


def test_no_missing_critical(df):
    for col in ["staff_id", "preferred_shift"]:
        assert df[col].isna().sum() == 0, f"{col} に欠損がある"

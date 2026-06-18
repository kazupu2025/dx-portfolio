# -*- coding: utf-8 -*-
"""
C-59 クレンジング出力テスト (10テスト以上)
"""

import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CLEANED_FILE = os.path.join(BASE_DIR, "output", "cleaned_farm_work_202401.csv")

REQUIRED_COLS = [
    "work_date", "record_id", "staff_id", "work_type", "crop",
    "work_hours", "target_qty", "actual_qty", "is_target_met",
    "achievement_rate", "productivity", "efficiency_grade", "source_file",
]


@pytest.fixture(scope="module")
def df():
    assert os.path.exists(CLEANED_FILE), f"File not found: {CLEANED_FILE}"
    return pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")


def test_file_exists():
    assert os.path.exists(CLEANED_FILE)


def test_row_count(df):
    assert len(df) >= 420, f"Expected >=420 rows, got {len(df)}"


def test_required_columns(df):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    assert missing == [], f"Missing columns: {missing}"


def test_work_date_format(df):
    parsed = pd.to_datetime(df["work_date"], format="%Y-%m-%d", errors="coerce")
    bad = parsed.isna().sum()
    assert bad == 0, f"Bad dates: {bad}"


def test_record_id_unique(df):
    dups = df["record_id"].duplicated().sum()
    assert dups == 0, f"Duplicate record_ids: {dups}"


def test_staff_id_variety(df):
    count = df["staff_id"].nunique()
    assert count >= 5, f"Expected >=5 staff, got {count}"


def test_work_type_variety(df):
    types = set(df["work_type"].dropna().unique())
    assert types == {"播種", "施肥", "収穫", "管理作業"}


def test_crop_variety(df):
    crops = set(df["crop"].dropna().unique())
    assert crops == {"トマト", "キュウリ", "レタス", "イチゴ", "ホウレンソウ"}


def test_work_hours_positive(df):
    assert (df["work_hours"] > 0).all()


def test_target_qty_positive(df):
    assert (df["target_qty"] > 0).all()


def test_actual_qty_nonneg(df):
    assert (df["actual_qty"] >= 0).all()


def test_is_target_met_binary(df):
    assert df["is_target_met"].isin([0, 1]).all()


def test_achievement_rate_nonneg(df):
    ar = df["achievement_rate"].dropna()
    assert (ar >= 0).all()


def test_productivity_nonneg(df):
    prod = df["productivity"].dropna()
    assert (prod >= 0).all()


def test_efficiency_grade_values(df):
    grades = set(df["efficiency_grade"].dropna().unique())
    assert grades == {"高効率", "中効率", "低効率"}


def test_source_file_variety(df):
    sources = set(df["source_file"].dropna().unique())
    assert sources == {"farm_work_styleA.csv", "farm_work_styleB.csv", "farm_work_styleC.csv"}


def test_no_null_work_date(df):
    assert df["work_date"].isna().sum() == 0


def test_met_count_positive(df):
    assert (df["is_target_met"] == 1).sum() >= 1

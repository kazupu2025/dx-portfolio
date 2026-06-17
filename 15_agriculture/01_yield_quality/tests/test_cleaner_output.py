# -*- coding: utf-8 -*-
"""
C-49 クレンジング出力テスト (10テスト以上)
"""

import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CLEANED_FILE = os.path.join(BASE_DIR, "output", "cleaned_harvest_202401.csv")

REQUIRED_COLS = [
    "harvest_date", "record_id", "farm_id", "farm_name",
    "crop", "harvest_qty", "grade_a_qty", "defect_qty",
    "inspector_id", "grade_a_rate", "defect_rate", "quality_flag", "source_file",
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


def test_harvest_date_format(df):
    parsed = pd.to_datetime(df["harvest_date"], format="%Y-%m-%d", errors="coerce")
    bad = parsed.isna().sum()
    assert bad == 0, f"Bad dates: {bad}"


def test_record_id_unique(df):
    dups = df["record_id"].duplicated().sum()
    assert dups == 0, f"Duplicate record_ids: {dups}"


def test_farm_name_variety(df):
    farms = set(df["farm_name"].dropna().unique())
    assert farms == {"農場A", "農場B", "農場C", "農場D"}


def test_crop_variety(df):
    crops = set(df["crop"].dropna().unique())
    assert crops == {"トマト", "キュウリ", "ピーマン", "レタス", "ほうれん草"}


def test_harvest_qty_positive(df):
    assert (df["harvest_qty"] > 0).all()


def test_grade_a_qty_nonneg(df):
    assert (df["grade_a_qty"] >= 0).all()


def test_defect_qty_nonneg(df):
    assert (df["defect_qty"] >= 0).all()


def test_grade_a_rate_range(df):
    r = df["grade_a_rate"].dropna()
    assert ((r >= 0) & (r <= 1)).all()


def test_defect_rate_range(df):
    dr = df["defect_rate"].dropna()
    assert ((dr >= 0) & (dr <= 1)).all()


def test_quality_flag_values(df):
    flags = set(df["quality_flag"].dropna().unique())
    assert flags == {"優良", "合格", "要改善"}


def test_source_file_variety(df):
    sources = set(df["source_file"].dropna().unique())
    assert sources == {"harvest_styleA.csv", "harvest_styleB.csv", "harvest_styleC.csv"}


def test_no_null_harvest_date(df):
    assert df["harvest_date"].isna().sum() == 0


def test_inspector_id_variety(df):
    assert df["inspector_id"].nunique() >= 3

# -*- coding: utf-8 -*-
"""
C-52: test_cleaner_output.py
cleaned_inquiries_202401.csv の品質を検証する (10テスト以上)。
"""
import re
import pytest
import pandas as pd
from pathlib import Path

CSV = Path("output/cleaned_inquiries_202401.csv")
REQUIRED_COLS = {
    "inquiry_date", "inquiry_id", "inquiry_type", "channel", "operator_id",
    "handling_minutes", "is_resolved", "recontact_flag", "satisfaction",
    "efficiency_flag", "cs_grade", "source_file",
}
VALID_TYPES = {"契約内容確認", "保険金請求", "解約手続き", "新規加入", "変更手続き"}
VALID_CHANNELS = {"電話", "メール", "窓口"}
VALID_EFFICIENCY = {"迅速", "標準", "長時間"}
VALID_CS_GRADE = {"高満足", "普通", "低満足"}


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(CSV, encoding="utf-8-sig")


# 1. CSV が存在する
def test_csv_exists():
    assert CSV.exists(), f"File not found: {CSV}"


# 2. 行数 >= 420
def test_row_count(df):
    assert len(df) >= 420, f"Row count insufficient: {len(df)}"


# 3. 必須列が存在する
def test_required_columns(df):
    missing = REQUIRED_COLS - set(df.columns)
    assert len(missing) == 0, f"Missing columns: {missing}"


# 4. inquiry_id に重複なし
def test_inquiry_id_unique(df):
    dup = df["inquiry_id"].duplicated().sum()
    assert dup == 0, f"Duplicate inquiry_id: {dup}"


# 5. inquiry_date が YYYY-MM-DD フォーマット
def test_inquiry_date_format(df):
    bad = df["inquiry_date"].dropna()[
        ~df["inquiry_date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")
    ]
    assert len(bad) == 0, f"Invalid dates: {len(bad)}"


# 6. inquiry_type が 5 種類
def test_inquiry_type_five_kinds(df):
    n = df["inquiry_type"].nunique()
    assert n >= 5, f"inquiry_type kinds insufficient: {n}"


# 7. channel が 3 種類
def test_channel_three_kinds(df):
    n = df["channel"].nunique()
    assert n >= 3, f"channel kinds insufficient: {n}"


# 8. handling_minutes が正値
def test_handling_minutes_positive(df):
    non_pos = (pd.to_numeric(df["handling_minutes"], errors="coerce") <= 0).sum()
    assert non_pos == 0, f"handling_minutes <= 0: {non_pos}"


# 9. is_resolved が 0/1 のみ
def test_is_resolved_binary(df):
    vals = pd.to_numeric(df["is_resolved"], errors="coerce").dropna()
    invalid = vals[~vals.isin([0, 1])]
    assert len(invalid) == 0, f"Invalid is_resolved values: {len(invalid)}"


# 10. recontact_flag が 0/1 のみ
def test_recontact_flag_binary(df):
    vals = pd.to_numeric(df["recontact_flag"], errors="coerce").dropna()
    invalid = vals[~vals.isin([0, 1])]
    assert len(invalid) == 0, f"Invalid recontact_flag values: {len(invalid)}"


# 11. satisfaction が 1〜5
def test_satisfaction_range(df):
    vals = pd.to_numeric(df["satisfaction"], errors="coerce").dropna()
    invalid = vals[(vals < 1) | (vals > 5)]
    assert len(invalid) == 0, f"Out of range satisfaction: {len(invalid)}"


# 12. efficiency_flag が 3 種類
def test_efficiency_flag_three_kinds(df):
    n = df["efficiency_flag"].nunique()
    assert n >= 3, f"efficiency_flag kinds insufficient: {n}"


# 13. cs_grade が 3 種類
def test_cs_grade_three_kinds(df):
    n = df["cs_grade"].nunique()
    assert n >= 3, f"cs_grade kinds insufficient: {n}"


# 14. source_file が 3 種類以上
def test_source_file_three_kinds(df):
    n = df["source_file"].nunique()
    assert n >= 3, f"source_file kinds insufficient: {n}"


# 15. 解決件数 >= 1
def test_resolved_exists(df):
    n = (pd.to_numeric(df["is_resolved"], errors="coerce") == 1).sum()
    assert n >= 1, "No resolved records found"


# 16. 未解決件数 >= 1
def test_unresolved_exists(df):
    n = (pd.to_numeric(df["is_resolved"], errors="coerce") == 0).sum()
    assert n >= 1, "No unresolved records found"


# 17. 再問い合わせ件数 >= 1
def test_recontact_exists(df):
    n = (pd.to_numeric(df["recontact_flag"], errors="coerce") == 1).sum()
    assert n >= 1, "No recontact records found"

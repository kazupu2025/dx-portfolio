# -*- coding: utf-8 -*-
"""
C-55 生徒入学申込・入学率分析パイプライン
クレンジング済みCSVのpytestテスト（10テスト以上）
"""

import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEANED_FILE = os.path.join(BASE_DIR, "output", "cleaned_applications_202401.csv")

# optional列（欠損率チェックから除外）
OPTIONAL_COLS = {"decline_reason"}

REQUIRED_COLS = [
    "app_date", "app_id", "department", "selection_method", "region",
    "result", "score", "interview_flag", "decline_reason",
    "is_enrolled", "score_grade", "source_file"
]


@pytest.fixture(scope="module")
def df():
    assert os.path.exists(CLEANED_FILE), f"クレンジング済みファイルが見つかりません: {CLEANED_FILE}"
    return pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")


# Test 1: ファイルが存在する
def test_file_exists():
    assert os.path.exists(CLEANED_FILE), "cleaned_applications_202401.csv が存在しない"


# Test 2: 行数が420以上
def test_row_count(df):
    assert len(df) >= 420, f"行数が420未満: {len(df)}"


# Test 3: 必須列がすべて存在する
def test_required_columns(df):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    assert len(missing) == 0, f"不足している列: {missing}"


# Test 4: app_date が YYYY-MM-DD 形式
def test_app_date_format(df):
    invalid = df["app_date"].dropna()[~df["app_date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")]
    assert len(invalid) == 0, f"不正な日付フォーマット: {invalid.tolist()[:5]}"


# Test 5: app_id が一意
def test_app_id_unique(df):
    assert df["app_id"].nunique() == len(df), "app_id に重複がある"


# Test 6: department が4種類
def test_department_values(df):
    expected = {"文系", "理系", "芸術系", "体育系"}
    actual = set(df["department"].dropna().unique())
    assert actual == expected, f"department の値が不正: {actual}"


# Test 7: selection_method が3種類
def test_selection_method_values(df):
    expected = {"一般", "推薦", "AO"}
    actual = set(df["selection_method"].dropna().unique())
    assert actual == expected, f"selection_method の値が不正: {actual}"


# Test 8: region が5種類
def test_region_values(df):
    expected = {"東京", "大阪", "名古屋", "福岡", "仙台"}
    actual = set(df["region"].dropna().unique())
    assert actual == expected, f"region の値が不正: {actual}"


# Test 9: score が [50, 100] の範囲
def test_score_range(df):
    scores = df["score"].dropna()
    assert scores.between(50, 100).all(), "score に範囲外の値がある"


# Test 10: interview_flag が 0 または 1 のみ
def test_interview_flag_values(df):
    vals = set(df["interview_flag"].dropna().astype(int).unique())
    assert vals.issubset({0, 1}), f"interview_flag に不正な値: {vals}"


# Test 11: is_enrolled が 0 または 1 のみ
def test_is_enrolled_values(df):
    vals = set(df["is_enrolled"].dropna().astype(int).unique())
    assert vals.issubset({0, 1}), f"is_enrolled に不正な値: {vals}"


# Test 12: score_grade が3種類
def test_score_grade_values(df):
    expected = {"高得点", "中得点", "低得点"}
    actual = set(df["score_grade"].dropna().unique())
    assert actual == expected, f"score_grade の値が不正: {actual}"


# Test 13: 欠損率が15%以下（optional列除く）
def test_null_rate(df):
    check_cols = [c for c in REQUIRED_COLS if c not in OPTIONAL_COLS and c in df.columns]
    for col in check_cols:
        rate = df[col].isnull().mean()
        assert rate <= 0.15, f"{col} の欠損率が15%超: {rate:.1%}"


# Test 14: decline_reason が不合格のみ設定（合格行は全てNaN）
def test_decline_reason_null_for_pass(df):
    pass_rows = df[df["result"] == "合格"]
    non_null = pass_rows["decline_reason"].dropna()
    non_empty = non_null[non_null.astype(str).str.strip() != ""]
    assert len(non_empty) == 0, f"合格行に decline_reason が設定されている: {len(non_empty)} 件"


# Test 15: source_file が3種類
def test_source_file_values(df):
    expected = {
        "applications_styleA.csv",
        "applications_styleB.csv",
        "applications_styleC.csv",
    }
    actual = set(df["source_file"].dropna().unique())
    assert actual == expected, f"source_file の値が不正: {actual}"

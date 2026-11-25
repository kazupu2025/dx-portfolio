import pandas as pd
import pytest
from pathlib import Path

BASE = Path(__file__).parent.parent
CSV = BASE / "output" / "cleaned_enrollment_202401.csv"

REQUIRED_COLS = {
    "enroll_date", "enroll_no", "course_name", "learner_type",
    "study_hours", "test_score", "status", "satisfaction",
    "source_file", "is_completed", "score_grade", "dropout_risk",
}

VALID_COURSES = {"Pythonプログラミング", "Excel基礎", "ビジネス英語", "プレゼン技術", "リーダーシップ"}
VALID_LEARNER_TYPES = {"新入社員", "中堅社員", "管理職"}
VALID_STATUSES = {"修了", "受講中", "中途離脱"}
VALID_SCORE_GRADES = {"優秀", "合格", "不合格"}
VALID_DROPOUT_RISKS = {"高", "低"}


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(CSV, encoding="utf-8-sig")


def test_csv_exists():
    assert CSV.exists(), f"{CSV} が存在しない"


def test_row_count(df):
    assert len(df) >= 420, f"行数が不足: {len(df)}"


def test_required_columns(df):
    missing = REQUIRED_COLS - set(df.columns)
    assert not missing, f"欠落列: {missing}"


def test_enroll_no_unique(df):
    dup = df["enroll_no"].duplicated().sum()
    assert dup == 0, f"重複enroll_no: {dup}"


def test_enroll_date_format(df):
    import re
    bad = df["enroll_date"].dropna()[
        ~df["enroll_date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")
    ]
    assert len(bad) == 0, f"不正な日付形式: {bad.head(3).tolist()}"


def test_course_name_variety(df):
    actual = set(df["course_name"].dropna().unique())
    assert actual == VALID_COURSES, f"course_name不一致: {actual}"


def test_learner_type_variety(df):
    actual = set(df["learner_type"].dropna().unique())
    assert actual == VALID_LEARNER_TYPES, f"learner_type不一致: {actual}"


def test_study_hours_positive(df):
    assert (df["study_hours"] > 0).all(), "study_hours に 0 以下の値あり"


def test_test_score_range(df):
    assert (df["test_score"] >= 0).all() and (df["test_score"] <= 100).all(), \
        "test_score が 0〜100 の範囲外"


def test_satisfaction_range(df):
    assert (df["satisfaction"] >= 1).all() and (df["satisfaction"] <= 5).all(), \
        "satisfaction が 1〜5 の範囲外"


def test_status_values(df):
    bad = ~df["status"].isin(VALID_STATUSES)
    assert bad.sum() == 0, f"不正なstatus: {df[bad]['status'].unique()}"


def test_is_completed_values(df):
    bad = ~df["is_completed"].isin({0, 1})
    assert bad.sum() == 0, f"不正なis_completed: {df[bad]['is_completed'].unique()}"


def test_score_grade_values(df):
    bad = ~df["score_grade"].isin(VALID_SCORE_GRADES)
    assert bad.sum() == 0, f"不正なscore_grade: {df[bad]['score_grade'].unique()}"


def test_dropout_risk_values(df):
    bad = ~df["dropout_risk"].isin(VALID_DROPOUT_RISKS)
    assert bad.sum() == 0, f"不正なdropout_risk: {df[bad]['dropout_risk'].unique()}"


def test_source_file_no_null(df):
    assert df["source_file"].notna().all(), "source_file に NULL あり"


def test_source_file_variety(df):
    n = df["source_file"].nunique()
    assert n == 3, f"source_file種類: {n} (期待: 3)"


def test_completed_count_positive(df):
    count = (df["is_completed"] == 1).sum()
    assert count >= 1, f"is_completed=1 の件数が 0"

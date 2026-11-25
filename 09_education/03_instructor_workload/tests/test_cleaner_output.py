import pandas as pd
import pytest
from pathlib import Path

BASE = Path(__file__).parent.parent
CSV = BASE / "output" / "cleaned_instructor_202401.csv"

REQUIRED_COLS = {
    "instructor_id", "name", "specialty", "employment_type",
    "session_date", "course_name", "lesson_count", "attendee_count",
    "venue", "hourly_rate", "source_file",
    "lesson_hours", "lesson_cost", "workload_flag",
}


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(CSV, encoding="utf-8-sig")


def test_csv_exists():
    assert CSV.exists(), f"{CSV} が存在しない"


def test_row_count(df):
    assert len(df) >= 400, f"行数が不足: {len(df)}"


def test_required_columns(df):
    missing = REQUIRED_COLS - set(df.columns)
    assert not missing, f"欠落列: {missing}"


def test_session_date_no_null(df):
    assert df["session_date"].notna().all(), "session_date に NULL あり"


def test_session_date_format(df):
    import re
    bad = df["session_date"].dropna()[
        ~df["session_date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")
    ]
    assert len(bad) == 0, f"不正な日付形式: {bad.head(3).tolist()}"


def test_instructor_id_no_null(df):
    assert df["instructor_id"].notna().all(), "instructor_id に NULL あり"


def test_instructor_id_variety(df):
    n = df["instructor_id"].nunique()
    assert n >= 15, f"講師ID種類が少ない: {n}"


def test_specialty_variety(df):
    n = df["specialty"].nunique()
    assert n >= 5, f"specialty種類が少ない: {n}"


def test_employment_type_variety(df):
    n = df["employment_type"].nunique()
    assert n == 3, f"employment_type種類: {n} (期待: 3)"


def test_lesson_count_positive(df):
    assert (df["lesson_count"] > 0).all(), "lesson_count に 0 以下の値あり"


def test_lesson_count_max4(df):
    assert (df["lesson_count"] <= 4).all(), "lesson_count が 4 を超える行あり"


def test_hourly_rate_positive(df):
    assert (df["hourly_rate"] > 0).all(), "hourly_rate に 0 以下の値あり"


def test_attendee_count_positive(df):
    assert (df["attendee_count"] > 0).all(), "attendee_count に 0 以下の値あり"


def test_lesson_cost_positive(df):
    assert (df["lesson_cost"] > 0).all(), "lesson_cost に 0 以下の値あり"


def test_workload_flag_values(df):
    valid = {"高負荷", "通常"}
    bad = ~df["workload_flag"].isin(valid)
    assert bad.sum() == 0, f"不正な workload_flag: {df[bad]['workload_flag'].unique()}"


def test_lesson_hours_calculation(df):
    diff = (df["lesson_hours"] - df["lesson_count"] * 1.5).abs()
    assert (diff < 0.01).all(), f"lesson_hours の計算ずれ: {(diff >= 0.01).sum()} 行"

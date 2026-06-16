"""
C-33: クレンジング出力の品質テスト (10テスト以上)
"""

import re
from pathlib import Path

import pandas as pd
import pytest

BASE_DIR = Path(__file__).parent.parent
CSV_PATH = BASE_DIR / "output" / "cleaned_recruitment_202401.csv"

REQUIRED_COLS = [
    "apply_date", "applicant_id", "job_type", "channel",
    "reached_phase", "hire_result", "screening_days",
    "is_hired", "phase_order", "passed_first_screen",
    "source_file",
]

VALID_JOB_TYPES = {"エンジニア", "営業", "事務", "マーケティング", "製造"}
VALID_CHANNELS = {"転職サイト", "エージェント", "リファラル", "自社HP"}
VALID_HIRE_RESULTS = {"採用", "不採用"}
VALID_PHASES = {"書類選考", "一次面接", "二次面接", "最終面接", "内定"}


@pytest.fixture(scope="module")
def df():
    assert CSV_PATH.exists(), f"CSV が存在しない: {CSV_PATH}"
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def test_csv_exists():
    assert CSV_PATH.exists(), f"CSV が存在しない: {CSV_PATH}"


def test_row_count(df):
    assert len(df) >= 400, f"行数不足: {len(df)}"


def test_required_columns(df):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    assert not missing, f"必須列が不足: {missing}"


def test_applicant_id_unique(df):
    dup_count = df["applicant_id"].duplicated().sum()
    assert dup_count == 0, f"applicant_id に重複が {dup_count} 件"


def test_apply_date_format(df):
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    invalid = df["apply_date"].dropna().apply(
        lambda v: not bool(pattern.match(str(v).strip()))
    )
    assert not invalid.any(), f"不正な apply_date が {invalid.sum()} 件"


def test_job_type_kinds(df):
    actual = set(df["job_type"].dropna().unique())
    assert actual == VALID_JOB_TYPES, \
        f"job_type が一致しない: 期待={VALID_JOB_TYPES}, 実際={actual}"


def test_channel_kinds(df):
    actual = set(df["channel"].dropna().unique())
    assert actual == VALID_CHANNELS, \
        f"channel が一致しない: 期待={VALID_CHANNELS}, 実際={actual}"


def test_hire_result_values(df):
    actual = set(df["hire_result"].dropna().unique())
    invalid = actual - VALID_HIRE_RESULTS
    assert not invalid, f"hire_result に無効値: {invalid}"


def test_is_hired_values(df):
    invalid = (~df["is_hired"].isin([0, 1])).sum()
    assert invalid == 0, f"is_hired に 0/1 以外の値が {invalid} 件"


def test_source_file_col(df):
    assert "source_file" in df.columns, "source_file 列が存在しない"
    assert df["source_file"].notna().all(), "source_file に NULL がある"
    n_files = df["source_file"].nunique()
    assert n_files == 3, f"source_file の種類数が3でない: {n_files}"


def test_screening_days_positive(df):
    invalid = (df["screening_days"] <= 0).sum()
    assert invalid == 0, f"screening_days <= 0 の行が {invalid} 件"


def test_phase_order_range(df):
    invalid = (~df["phase_order"].isin([1, 2, 3, 4, 5])).sum()
    assert invalid == 0, f"phase_order が 1〜5 以外の行が {invalid} 件"


def test_hired_applicants_have_naitei_phase(df):
    """採用者(is_hired=1)の全員が内定フェーズに到達している"""
    hired_rows = df[df["is_hired"] == 1]
    if len(hired_rows) > 0:
        not_naitei = (hired_rows["reached_phase"] != "内定").sum()
        assert not_naitei == 0, f"採用者で内定未到達の行が {not_naitei} 件"

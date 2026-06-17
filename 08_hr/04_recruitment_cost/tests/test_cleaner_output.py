"""
C-41: クレンジング出力の品質テスト (10テスト以上)
"""

import re
from pathlib import Path

import pandas as pd
import pytest

BASE_DIR = Path(__file__).parent.parent
CSV_PATH = BASE_DIR / "output" / "cleaned_recruitment_202401.csv"

REQUIRED_COLS = [
    "apply_date", "apply_no", "channel", "job_type",
    "cost", "phase", "is_hired", "is_accepted",
    "cost_per_hire", "channel_efficiency", "offer_acceptance",
    "source_file",
]

VALID_CHANNELS = {"求人サイト", "SNS採用", "リファラル", "エージェント", "合同説明会"}
VALID_JOB_TYPES = {"エンジニア", "営業", "事務", "マーケ", "デザイン"}
VALID_PHASES = {"書類選考", "一次面接", "二次面接", "最終面接", "内定"}
VALID_EFFICIENCY = {"高効率", "標準"}
VALID_OFFER_ACCEPTANCE = {"承諾", "辞退", "該当なし"}


@pytest.fixture(scope="module")
def df():
    assert CSV_PATH.exists(), f"CSV が存在しない: {CSV_PATH}"
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def test_csv_exists():
    assert CSV_PATH.exists(), f"CSV が存在しない: {CSV_PATH}"


def test_row_count(df):
    assert len(df) >= 420, f"行数不足: {len(df)}"


def test_required_columns(df):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    assert not missing, f"必須列が不足: {missing}"


def test_apply_no_unique(df):
    dup_count = df["apply_no"].duplicated().sum()
    assert dup_count == 0, f"apply_no に重複が {dup_count} 件"


def test_apply_date_format(df):
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    invalid = df["apply_date"].dropna().apply(
        lambda v: not bool(pattern.match(str(v).strip()))
    )
    assert not invalid.any(), f"不正な apply_date が {invalid.sum()} 件"


def test_channel_kinds(df):
    actual = set(df["channel"].dropna().unique())
    assert actual == VALID_CHANNELS, \
        f"channel が一致しない: 期待={VALID_CHANNELS}, 実際={actual}"


def test_job_type_kinds(df):
    actual = set(df["job_type"].dropna().unique())
    assert actual == VALID_JOB_TYPES, \
        f"job_type が一致しない: 期待={VALID_JOB_TYPES}, 実際={actual}"


def test_cost_positive(df):
    invalid = (df["cost"] <= 0).sum()
    assert invalid == 0, f"cost <= 0 の行が {invalid} 件"


def test_phase_values(df):
    actual = set(df["phase"].dropna().unique())
    invalid = actual - VALID_PHASES
    assert not invalid, f"phase に無効値: {invalid}"


def test_is_hired_values(df):
    invalid = (~df["is_hired"].isin([0, 1])).sum()
    assert invalid == 0, f"is_hired に 0/1 以外の値が {invalid} 件"


def test_is_accepted_values(df):
    not_na = df["is_accepted"].dropna()
    invalid = (~not_na.isin([0, 1])).sum()
    assert invalid == 0, f"is_accepted に 0/1/NaN 以外の値が {invalid} 件"


def test_channel_efficiency_values(df):
    actual = set(df["channel_efficiency"].dropna().unique())
    invalid = actual - VALID_EFFICIENCY
    assert not invalid, f"channel_efficiency に無効値: {invalid}"


def test_offer_acceptance_values(df):
    actual = set(df["offer_acceptance"].dropna().unique())
    invalid = actual - VALID_OFFER_ACCEPTANCE
    assert not invalid, f"offer_acceptance に無効値: {invalid}"


def test_source_file_col(df):
    assert "source_file" in df.columns, "source_file 列が存在しない"
    assert df["source_file"].notna().all(), "source_file に NULL がある"
    n_files = df["source_file"].nunique()
    assert n_files == 3, f"source_file の種類数が3でない: {n_files}"


def test_cost_per_hire_equals_cost(df):
    """cost_per_hire は cost と等しい"""
    mismatch = (df["cost"] != df["cost_per_hire"]).sum()
    assert mismatch == 0, f"cost_per_hire と cost が一致しない行が {mismatch} 件"


def test_hired_count_positive(df):
    """採用件数 >= 1"""
    hired_count = (df["is_hired"] == 1).sum()
    assert hired_count >= 1, f"採用件数が 0 件"


def test_cost_max_reasonable(df):
    """コスト最大値 <= 1,000,000"""
    max_cost = df["cost"].max()
    assert max_cost <= 1_000_000, f"コスト最大値が上限超過: {max_cost}"

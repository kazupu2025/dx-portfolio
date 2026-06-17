# -*- coding: utf-8 -*-
import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "output", "cleaned_claims_202401.csv")

CANONICAL_COLS = [
    "claim_date", "claim_id", "dept", "insurance_type",
    "patient_count", "total_points", "claim_amount", "reduction_amount",
    "payment_status", "net_amount", "reduction_rate",
    "is_returned", "collection_flag", "source_file"
]


@pytest.fixture(scope="module")
def df():
    assert os.path.exists(CSV_PATH), "cleaned_claims_202401.csv not found"
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def test_file_exists():
    assert os.path.exists(CSV_PATH)


def test_row_count(df):
    assert len(df) >= 420


def test_canonical_columns(df):
    for col in CANONICAL_COLS:
        assert col in df.columns, "Missing column: {}".format(col)


def test_claim_date_format(df):
    ok = df["claim_date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")
    assert ok.all()


def test_claim_id_unique(df):
    assert df["claim_id"].nunique() == len(df)


def test_dept_5_kinds(df):
    assert df["dept"].nunique() == 5


def test_insurance_type_3_kinds(df):
    assert df["insurance_type"].nunique() == 3


def test_net_amount_nonnegative(df):
    assert (df["net_amount"] >= 0).all()


def test_reduction_rate_range(df):
    assert ((df["reduction_rate"] >= 0) & (df["reduction_rate"] <= 1)).all()


def test_is_returned_binary(df):
    assert df["is_returned"].isin([0, 1]).all()


def test_collection_flag_2_kinds(df):
    assert df["collection_flag"].nunique() == 2


def test_source_file_3_kinds(df):
    assert df["source_file"].nunique() == 3


def test_patient_count_positive(df):
    assert (df["patient_count"] >= 1).all()


def test_total_points_positive(df):
    assert (df["total_points"] > 0).all()


def test_claim_amount_positive(df):
    assert (df["claim_amount"] > 0).all()

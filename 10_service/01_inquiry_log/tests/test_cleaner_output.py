"""
B-15 クレンジング出力テスト (14テスト)
"""
import pytest
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CSV_PATH = BASE / "output" / "cleaned_inquiry_202401.csv"
CFG_PATH = BASE / "config.yml"
import yaml
with open(CFG_PATH, encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

VALID_CATEGORIES  = {"請求・支払い", "製品不具合", "使い方・操作方法", "配送・到着", "返品・交換", "その他"}
VALID_RESOLUTIONS = {"解決済", "対応中", "未解決", "エスカレ済"}
VALID_CHANNELS    = {"電話", "メール", "チャット", "SNS"}


@pytest.fixture(scope="module")
def df():
    assert CSV_PATH.exists(), f"CSV not found: {CSV_PATH}"
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def test_csv_exists():
    assert CSV_PATH.exists()


def test_row_count(df):
    assert cfg["min_rows"] <= len(df) <= cfg["max_rows"], f"rows={len(df)}"


def test_required_columns(df):
    required = [
        "inquiry_id", "received_at", "completed_at",
        "operator_id", "operator_name", "channel",
        "inquiry_text", "category", "resolution",
        "escalation", "response_minutes", "is_resolved", "is_escalated"
    ]
    missing = [c for c in required if c not in df.columns]
    assert not missing, f"Missing columns: {missing}"


def test_inquiry_id_no_null(df):
    assert df["inquiry_id"].isna().sum() == 0


def test_received_at_no_null(df):
    assert df["received_at"].isna().sum() == 0


def test_operator_id_no_null(df):
    assert df["operator_id"].isna().sum() == 0


def test_category_no_null(df):
    assert df["category"].isna().sum() == 0


def test_resolution_no_null(df):
    assert df["resolution"].isna().sum() == 0


def test_response_minutes_positive(df):
    vals = pd.to_numeric(df["response_minutes"], errors="coerce")
    assert (vals > 0).all(), f"Non-positive response_minutes found"


def test_category_values(df):
    invalid = set(df["category"].unique()) - VALID_CATEGORIES
    assert not invalid, f"Invalid categories: {invalid}"


def test_resolution_values(df):
    invalid = set(df["resolution"].unique()) - VALID_RESOLUTIONS
    assert not invalid, f"Invalid resolutions: {invalid}"


def test_channel_values(df):
    invalid = set(df["channel"].unique()) - VALID_CHANNELS
    assert not invalid, f"Invalid channels: {invalid}"


def test_operator_count(df):
    count = df["operator_id"].nunique()
    assert count == cfg["expected_operator_count"], f"operator count={count}"


def test_category_count(df):
    count = df["category"].nunique()
    assert count == cfg["expected_category_count"], f"category count={count}"

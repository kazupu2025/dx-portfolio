# -*- coding: utf-8 -*-
import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "output", "cleaned_reservations_202401.csv")

CANONICAL_COLS = [
    "checkin_date", "reserv_no", "room_type", "guest_count", "nights",
    "room_rate", "status", "cancel_reason", "total_revenue", "is_cancel",
    "loss_revenue", "revenue_per_guest", "source_file"
]


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def test_file_exists():
    assert os.path.exists(CSV_PATH), "cleaned_reservations_202401.csv not found"


def test_row_count(df):
    assert len(df) >= 420, f"Expected >= 420 rows, got {len(df)}"


def test_canonical_columns(df):
    for col in CANONICAL_COLS:
        assert col in df.columns, f"Missing column: {col}"


def test_checkin_date_format(df):
    parsed = pd.to_datetime(df["checkin_date"], format="%Y-%m-%d", errors="coerce")
    assert parsed.isnull().sum() == 0, "Some checkin_date values are not YYYY-MM-DD"


def test_reserv_no_unique(df):
    assert df["reserv_no"].is_unique, "reserv_no has duplicates"


def test_room_type_values(df):
    expected = {"シングル", "ツイン", "ダブル", "スイート"}
    actual = set(df["room_type"].unique())
    assert actual == expected, f"Unexpected room_types: {actual}"


def test_status_values(df):
    expected = {"宿泊済み", "キャンセル", "ノーショウ"}
    actual = set(df["status"].unique())
    assert actual == expected, f"Unexpected statuses: {actual}"


def test_guest_count_positive(df):
    assert (df["guest_count"] >= 1).all(), "guest_count has values < 1"


def test_nights_positive(df):
    assert (df["nights"] >= 1).all(), "nights has values < 1"


def test_room_rate_positive(df):
    assert (df["room_rate"] > 0).all(), "room_rate has zero or negative values"


def test_total_revenue_non_negative(df):
    assert (df["total_revenue"] >= 0).all(), "total_revenue has negative values"


def test_is_cancel_binary(df):
    assert df["is_cancel"].isin([0, 1]).all(), "is_cancel has values other than 0 or 1"


def test_loss_revenue_non_negative(df):
    assert (df["loss_revenue"] >= 0).all(), "loss_revenue has negative values"


def test_source_file_three_styles(df):
    expected = {"styleA", "styleB", "styleC"}
    actual = set(df["source_file"].unique())
    assert actual == expected, f"Unexpected source_file values: {actual}"


def test_cancel_exists(df):
    assert (df["status"] == "キャンセル").sum() >= 1, "No cancelled reservations found"


def test_noshow_exists(df):
    assert (df["status"] == "ノーショウ").sum() >= 1, "No no-show reservations found"


def test_stayed_exists(df):
    assert (df["status"] == "宿泊済み").sum() >= 1, "No stayed reservations found"


def test_total_revenue_zero_for_cancel(df):
    cancel_rows = df[df["is_cancel"] == 1]
    assert (cancel_rows["total_revenue"] == 0).all(), "Cancelled rows should have total_revenue == 0"


def test_loss_revenue_for_cancel(df):
    cancel_rows = df[df["is_cancel"] == 1]
    expected = cancel_rows["room_rate"] * cancel_rows["nights"]
    assert (cancel_rows["loss_revenue"] == expected).all(), "loss_revenue mismatch for cancelled rows"

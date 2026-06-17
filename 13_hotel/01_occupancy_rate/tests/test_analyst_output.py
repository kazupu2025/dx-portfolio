# -*- coding: utf-8 -*-
import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
ROOM_CSV = os.path.join(OUTPUT_DIR, "room_summary_202401.csv")
REPORT_MD = os.path.join(OUTPUT_DIR, "analysis_report.md")


@pytest.fixture(scope="module")
def room_df():
    return pd.read_csv(ROOM_CSV, encoding="utf-8-sig")


def test_room_summary_exists():
    assert os.path.exists(ROOM_CSV), "room_summary_202401.csv not found"


def test_report_exists():
    assert os.path.exists(REPORT_MD), "analysis_report.md not found"


def test_room_summary_four_rows(room_df):
    assert len(room_df) == 4, f"Expected 4 rows, got {len(room_df)}"


def test_room_type_column(room_df):
    assert "room_type" in room_df.columns


def test_total_revenue_positive(room_df):
    assert (room_df["total_revenue"] > 0).any(), "All total_revenue are zero"


def test_occupancy_rate_valid(room_df):
    assert "occupancy_rate" in room_df.columns
    assert room_df["occupancy_rate"].between(0, 1).all(), "occupancy_rate out of [0,1]"


def test_cancel_rate_valid(room_df):
    assert "cancel_rate" in room_df.columns
    assert room_df["cancel_rate"].between(0, 1).all(), "cancel_rate out of [0,1]"


def test_report_contains_summary():
    with open(REPORT_MD, "r", encoding="utf-8") as f:
        content = f.read()
    assert "総合サマリー" in content


def test_report_contains_room_section():
    with open(REPORT_MD, "r", encoding="utf-8") as f:
        content = f.read()
    assert "客室タイプ別分析" in content

# -*- coding: utf-8 -*-
"""
C-38: 分析出力テスト (7テスト以上)
"""

import json
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"

REPORT_FILE = OUTPUT_DIR / "analysis_report.md"
STORE_CSV = OUTPUT_DIR / "store_summary_202401.csv"
JSON_FILE = OUTPUT_DIR / "result_analysis.json"


@pytest.fixture(scope="module")
def store_df():
    assert STORE_CSV.exists(), f"File not found: {STORE_CSV}"
    return pd.read_csv(STORE_CSV, encoding="utf-8-sig")


@pytest.fixture(scope="module")
def summary_json():
    assert JSON_FILE.exists(), f"File not found: {JSON_FILE}"
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def report_content():
    assert REPORT_FILE.exists(), f"File not found: {REPORT_FILE}"
    return REPORT_FILE.read_text(encoding="utf-8")


def test_01_report_exists():
    """analysis_report.md が存在する"""
    assert REPORT_FILE.exists(), f"Report not found: {REPORT_FILE}"


def test_02_store_summary_exists():
    """store_summary_202401.csv が存在する"""
    assert STORE_CSV.exists(), f"Store summary not found: {STORE_CSV}"


def test_03_json_exists():
    """result_analysis.json が存在する"""
    assert JSON_FILE.exists(), f"JSON not found: {JSON_FILE}"


def test_04_json_required_keys(summary_json):
    """result_analysis.json に必須キーが存在する"""
    required = {"total_reserv", "cancel_count", "cancel_rate", "loss_amount_total"}
    missing = required - summary_json.keys()
    assert missing == set(), f"Missing JSON keys: {missing}"


def test_05_cancel_rate_range(summary_json):
    """cancel_rate が 0~100 の範囲内である"""
    rate = summary_json["cancel_rate"]
    assert 0 <= rate <= 100, f"cancel_rate out of range: {rate}"


def test_06_loss_amount_non_negative(summary_json):
    """loss_amount_total が非負である"""
    assert summary_json["loss_amount_total"] >= 0


def test_07_store_summary_has_three_stores(store_df):
    """店舗サマリーに3店舗分のデータがある"""
    assert len(store_df) == 3, f"Expected 3 stores, got {len(store_df)}"


def test_08_store_summary_cancel_rate_column(store_df):
    """店舗サマリーに cancel_rate 列がある"""
    assert "cancel_rate" in store_df.columns


def test_09_report_contains_insights(report_content):
    """レポートにインサイトセクションが含まれる"""
    assert "インサイト" in report_content or "改善" in report_content


def test_10_store_summary_loss_amount_non_negative(store_df):
    """店舗サマリーの損失金額列が全て非負である"""
    assert "loss_amount_total" in store_df.columns
    assert (store_df["loss_amount_total"] >= 0).all()


def test_11_total_reserv_positive(summary_json):
    """total_reserv が正の整数である"""
    assert summary_json["total_reserv"] > 0

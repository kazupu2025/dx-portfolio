# -*- coding: utf-8 -*-
"""
test_analyst_output.py

analyze.py の出力（analysis_report.md, store_summary_202401.csv, result_analysis.json）
を検証するテスト群。
pytest で実行: pytest tests/test_analyst_output.py -v
"""

import json
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
STORE_CSV_PATH = OUTPUT_DIR / "store_summary_202401.csv"
JSON_PATH = OUTPUT_DIR / "result_analysis.json"


# ---- フィクスチャ --------------------------------------------------------

@pytest.fixture(scope="module")
def report_text() -> str:
    if not REPORT_PATH.exists():
        pytest.skip(f"レポートが存在しません: {REPORT_PATH}")
    return REPORT_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def store_df() -> pd.DataFrame:
    if not STORE_CSV_PATH.exists():
        pytest.skip(f"CSVが存在しません: {STORE_CSV_PATH}")
    return pd.read_csv(STORE_CSV_PATH, encoding="utf-8-sig")


@pytest.fixture(scope="module")
def analysis_json() -> dict:
    if not JSON_PATH.exists():
        pytest.skip(f"JSONが存在しません: {JSON_PATH}")
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))


# ---- レポートテスト -------------------------------------------------------

def test_report_exists():
    """analysis_report.md が存在する。"""
    assert REPORT_PATH.exists(), f"レポートが見つかりません: {REPORT_PATH}"


def test_report_not_empty(report_text):
    """レポートが空でない（100文字以上）。"""
    assert len(report_text) > 100, f"レポートが短すぎます: {len(report_text)} 文字"


def test_report_has_title(report_text):
    """レポートにタイトル行が含まれる。"""
    assert "# 返品" in report_text


def test_report_has_store_section(report_text):
    """店舗別セクションが存在する。"""
    assert "店舗別" in report_text


def test_report_has_claim_type_section(report_text):
    """クレーム区分セクションが存在する。"""
    assert "クレーム区分" in report_text


def test_report_has_insights(report_text):
    """インサイト・改善示唆セクションが存在する。"""
    assert ("インサイト" in report_text) or ("改善示唆" in report_text)


def test_report_has_markdown_table(report_text):
    """Markdown テーブルが含まれる。"""
    assert "|" in report_text and "---" in report_text


# ---- 店舗サマリー CSV テスト ----------------------------------------------

def test_store_csv_exists():
    """store_summary_202401.csv が存在する。"""
    assert STORE_CSV_PATH.exists(), f"CSVが見つかりません: {STORE_CSV_PATH}"


def test_store_csv_row_count(store_df):
    """5 店舗分のデータがある。"""
    assert len(store_df) == 5, f"店舗数: {len(store_df)}"


def test_store_csv_has_claim_count_column(store_df):
    """クレーム件数列が存在する。"""
    assert "クレーム件数" in store_df.columns


def test_store_csv_has_resolve_rate_column(store_df):
    """解決率列が存在する。"""
    assert "解決率" in store_df.columns


def test_store_csv_has_avg_amount_column(store_df):
    """平均返品金額列が存在する。"""
    assert "平均返品金額" in store_df.columns


# ---- JSON テスト ----------------------------------------------------------

def test_json_exists():
    """result_analysis.json が存在する。"""
    assert JSON_PATH.exists(), f"JSONが見つかりません: {JSON_PATH}"


def test_json_has_required_keys(analysis_json):
    """JSON に必須キーが存在する。"""
    required = ["total_claims", "resolved_count", "resolve_rate", "avg_response_days", "total_return_amount"]
    missing = [k for k in required if k not in analysis_json]
    assert not missing, f"不足キー: {missing}"


def test_json_resolve_rate_valid(analysis_json):
    """解決率が 70% 以上 100% 以下。"""
    rate = analysis_json.get("resolve_rate", 0)
    assert 70 <= rate <= 100, f"解決率が範囲外: {rate}"


def test_json_total_claims_positive(analysis_json):
    """総クレーム数が正の値。"""
    total = analysis_json.get("total_claims", 0)
    assert total > 0, f"総クレーム数が 0 以下: {total}"


def test_json_store_summary_list(analysis_json):
    """store_summary が 5 店舗のリスト。"""
    store_list = analysis_json.get("store_summary", [])
    assert len(store_list) == 5, f"store_summary の長さ: {len(store_list)}"

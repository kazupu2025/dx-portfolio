# -*- coding: utf-8 -*-
"""
C-60 IT/SaaS - カスタマーサポートチケット分析
分析出力テスト (7テスト以上)
"""

import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
REPORT_PATH = os.path.join(OUTPUT_DIR, "analysis_report.md")
CAT_CSV_PATH = os.path.join(OUTPUT_DIR, "category_summary_202401.csv")

EXPECTED_CATEGORIES = {"ログイン障害", "機能不具合", "請求問い合わせ", "使い方質問", "データ移行"}


def test_report_exists():
    """analysis_report.mdが存在する"""
    assert os.path.exists(REPORT_PATH), f"レポートが見つかりません: {REPORT_PATH}"


def test_category_csv_exists():
    """category_summary_202401.csvが存在する"""
    assert os.path.exists(CAT_CSV_PATH), f"CSVが見つかりません: {CAT_CSV_PATH}"


def test_report_has_summary_section():
    """レポートに全体サマリーセクションがある"""
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "全体サマリー" in content


def test_report_has_category_section():
    """レポートにカテゴリ別分析セクションがある"""
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "カテゴリ別分析" in content


def test_report_has_priority_section():
    """レポートに優先度別分析セクションがある"""
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "優先度別分析" in content


def test_report_has_agent_section():
    """レポートに担当者別分析セクションがある"""
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "担当者別分析" in content


@pytest.fixture(scope="module")
def cat_df():
    assert os.path.exists(CAT_CSV_PATH), f"CSVが見つかりません: {CAT_CSV_PATH}"
    return pd.read_csv(CAT_CSV_PATH, encoding="utf-8-sig")


def test_category_csv_has_all_categories(cat_df):
    """カテゴリサマリーに5カテゴリ含まれる"""
    actual = set(cat_df["category"].unique())
    assert EXPECTED_CATEGORIES <= actual, f"不足カテゴリ: {EXPECTED_CATEGORIES - actual}"


def test_category_csv_required_columns(cat_df):
    """カテゴリサマリーに必須列が存在する"""
    required = {"category", "count", "resolve_rate", "avg_resolution_hours", "avg_satisfaction"}
    missing = required - set(cat_df.columns)
    assert missing == set(), f"不足列: {missing}"


def test_category_csv_count_total(cat_df):
    """カテゴリサマリーの件数合計が420以上"""
    assert cat_df["count"].sum() >= 420, f"件数合計: {cat_df['count'].sum()}"


def test_category_csv_resolve_rate_range(cat_df):
    """解決率が0〜1の範囲"""
    assert ((cat_df["resolve_rate"] >= 0) & (cat_df["resolve_rate"] <= 1)).all()

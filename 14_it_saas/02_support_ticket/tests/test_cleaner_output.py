# -*- coding: utf-8 -*-
"""
C-60 IT/SaaS - カスタマーサポートチケット分析
クレンジング出力テスト (10テスト以上)
"""

import os
import re
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CLEANED_PATH = os.path.join(BASE_DIR, "output", "cleaned_tickets_202401.csv")

REQUIRED_COLS = [
    "received_date", "ticket_id", "category", "priority", "agent_id",
    "resolution_hours", "is_escalated", "escalation_reason",
    "satisfaction", "is_resolved", "speed_grade", "cs_level", "source_file"
]
EXPECTED_CATEGORIES = {"ログイン障害", "機能不具合", "請求問い合わせ", "使い方質問", "データ移行"}
EXPECTED_PRIORITIES = {"高", "中", "低"}
EXPECTED_SPEED_GRADES = {"迅速", "標準", "長時間"}
EXPECTED_CS_LEVELS = {"高満足", "普通", "低満足"}
# escalation_reason は optional（欠損率チェック除外）
OPTIONAL_COLS = {"escalation_reason"}


@pytest.fixture(scope="module")
def df():
    assert os.path.exists(CLEANED_PATH), f"クレンジング済みファイルが見つかりません: {CLEANED_PATH}"
    _df = pd.read_csv(CLEANED_PATH, encoding="utf-8-sig")
    _df["resolution_hours"] = pd.to_numeric(_df["resolution_hours"], errors="coerce")
    _df["is_escalated"] = pd.to_numeric(_df["is_escalated"], errors="coerce")
    _df["satisfaction"] = pd.to_numeric(_df["satisfaction"], errors="coerce")
    _df["is_resolved"] = pd.to_numeric(_df["is_resolved"], errors="coerce")
    return _df


def test_file_exists():
    """クレンジング済みファイルが存在する"""
    assert os.path.exists(CLEANED_PATH)


def test_row_count(df):
    """行数が420以上"""
    assert len(df) >= 420, f"行数不足: {len(df)}"


def test_required_columns(df):
    """必須列がすべて存在する"""
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    assert missing == [], f"不足列: {missing}"


def test_received_date_format(df):
    """received_dateがYYYY-MM-DD形式"""
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    invalid = df["received_date"].dropna()[
        ~df["received_date"].dropna().apply(lambda x: bool(pattern.match(str(x))))
    ]
    assert len(invalid) == 0, f"不正な日付: {invalid.head(5).tolist()}"


def test_ticket_id_unique(df):
    """ticket_idが一意"""
    assert df["ticket_id"].nunique() == len(df), "ticket_idに重複あり"


def test_category_values(df):
    """categoryが5種類含まれる"""
    actual = set(df["category"].dropna().unique())
    assert EXPECTED_CATEGORIES <= actual, f"不足カテゴリ: {EXPECTED_CATEGORIES - actual}"


def test_priority_values(df):
    """priorityが高/中/低のみ"""
    actual = set(df["priority"].dropna().unique())
    assert actual <= EXPECTED_PRIORITIES, f"想定外の優先度: {actual - EXPECTED_PRIORITIES}"


def test_agent_id_variety(df):
    """agent_idの種類が4以上"""
    assert df["agent_id"].nunique() >= 4, f"agent_idの種類不足: {df['agent_id'].nunique()}"


def test_resolution_hours_positive(df):
    """resolution_hoursがすべて>0"""
    rh = df["resolution_hours"].dropna()
    assert (rh > 0).all(), f"resolution_hours<=0の件数: {(rh <= 0).sum()}"


def test_is_escalated_binary(df):
    """is_escalatedが0/1のみ"""
    vals = set(df["is_escalated"].dropna().astype(int).unique())
    assert vals <= {0, 1}, f"想定外のis_escalated値: {vals}"


def test_satisfaction_range(df):
    """satisfactionが1〜5の範囲"""
    sat = df["satisfaction"].dropna()
    assert ((sat >= 1) & (sat <= 5)).all(), "satisfactionが1〜5の範囲外"


def test_is_resolved_binary(df):
    """is_resolvedが0/1のみ"""
    vals = set(df["is_resolved"].dropna().astype(int).unique())
    assert vals <= {0, 1}, f"想定外のis_resolved値: {vals}"


def test_speed_grade_values(df):
    """speed_gradeが3種類含まれる"""
    actual = set(df["speed_grade"].dropna().unique())
    assert EXPECTED_SPEED_GRADES <= actual, f"不足speed_grade: {EXPECTED_SPEED_GRADES - actual}"


def test_cs_level_values(df):
    """cs_levelが3種類含まれる"""
    actual = set(df["cs_level"].dropna().unique())
    assert EXPECTED_CS_LEVELS <= actual, f"不足cs_level: {EXPECTED_CS_LEVELS - actual}"


def test_null_rate_required_cols(df):
    """必須列（escalation_reason除く）の欠損率が15%以下"""
    check_cols = [c for c in REQUIRED_COLS if c not in OPTIONAL_COLS and c in df.columns]
    for col in check_cols:
        rate = df[col].isna().mean()
        assert rate <= 0.15, f"{col}の欠損率が15%超: {rate:.1%}"


def test_source_file_variety(df):
    """source_fileが3種類"""
    assert df["source_file"].nunique() == 3, f"source_file種類数: {df['source_file'].nunique()}"


def test_escalation_reason_nullable(df):
    """escalation_reasonはエスカレーション時のみ設定されている（null許容）"""
    # エスカレーションあり -> escalation_reasonはnullでない
    esc_rows = df[df["is_escalated"] == 1]
    # エスカレーション時に理由が設定されているか（一部nullでも許容するが大半が設定済みであること）
    if len(esc_rows) > 0:
        reason_filled_rate = esc_rows["escalation_reason"].notna().mean()
        assert reason_filled_rate >= 0.5, f"エスカレーション時のescalation_reason設定率が低い: {reason_filled_rate:.1%}"


def test_resolved_count_positive(df):
    """解決件数が1以上"""
    resolved = int(df["is_resolved"].sum())
    assert resolved >= 1, "解決件数が0"


def test_escalated_count_positive(df):
    """エスカレーション件数が1以上"""
    esc = int(df["is_escalated"].sum())
    assert esc >= 1, "エスカレーション件数が0"

import sys
from pathlib import Path
import pandas as pd
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyze import analyze, REQUIRED_COLUMNS


@pytest.fixture
def sample_df():
    """テスト用のサンプルデータを作成"""
    return pd.DataFrame({
        "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05",
                 "2024-01-06", "2024-01-07", "2024-01-08", "2024-01-09", "2024-01-10"],
        "event_type": ["婚礼", "忘年会", "新年会", "会議", "懇親会", "婚礼", "新年会", "会議", "懇親会", "婚礼"],
        "room_name": ["鳳凰の間", "桜の間", "梅の間", "会議室A", "桜の間", "鳳凰の間", "梅の間", "会議室A", "桜の間", "鳳凰の間"],
        "guests": [100, 80, 60, 30, 90, 120, 70, 50, 100, 110],
        "food_revenue": [500000, 400000, 300000, 150000, 450000, 600000, 350000, 250000, 500000, 550000],
        "beverage_revenue": [100000, 80000, 60000, 30000, 90000, 120000, 70000, 50000, 100000, 110000],
        "room_fee": [50000, 40000, 30000, 0, 40000, 60000, 30000, 20000, 50000, 55000],
        "total_revenue": [650000, 520000, 390000, 180000, 580000, 780000, 450000, 320000, 650000, 715000],
        "status": ["完了", "完了", "完了", "完了", "完了", "完了", "完了", "完了", "完了", "完了"],
    })


def test_returns_dict(sample_df):
    """analyze()が辞書を返すことをテスト"""
    result = analyze(sample_df)
    assert isinstance(result, dict)


def test_required_keys(sample_df):
    """返された辞書に必要なキーが含まれることをテスト"""
    result = analyze(sample_df)
    required_keys = [
        "df",
        "event_df",
        "room_df",
        "monthly_df",
        "total_revenue",
        "total_events",
        "avg_revenue_per_event",
        "avg_revenue_per_guest",
        "cancel_rate",
        "verdict",
    ]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"


def test_verdict_good(sample_df):
    """1名単価≥15000の場合、verdictが'good'であることをテスト"""
    # 高単価のデータを作成
    high_price_df = pd.DataFrame({
        "date": ["2024-01-01", "2024-01-02"],
        "event_type": ["婚礼", "婚礼"],
        "room_name": ["鳳凰の間", "鳳凰の間"],
        "guests": [50, 60],
        "food_revenue": [1000000, 1200000],
        "beverage_revenue": [200000, 250000],
        "room_fee": [100000, 120000],
        "total_revenue": [1300000, 1570000],
        "status": ["完了", "完了"],
    })
    result = analyze(high_price_df)
    assert result["verdict"] == "good"


def test_verdict_warning(sample_df):
    """8000≤1名単価<15000の場合、verdictが'warning'であることをテスト"""
    # 中程度単価のデータを作成（単価 = (640000 + 930000) / (80 + 100) = 10500円）
    mid_price_df = pd.DataFrame({
        "date": ["2024-01-01", "2024-01-02"],
        "event_type": ["懇親会", "懇親会"],
        "room_name": ["桜の間", "桜の間"],
        "guests": [80, 100],
        "food_revenue": [400000, 500000],
        "beverage_revenue": [120000, 200000],
        "room_fee": [120000, 230000],
        "total_revenue": [640000, 930000],
        "status": ["完了", "完了"],
    })
    result = analyze(mid_price_df)
    assert result["verdict"] == "warning"


def test_verdict_alert(sample_df):
    """1名単価<8000の場合、verdictが'alert'であることをテスト"""
    # 低単価のデータを作成
    low_price_df = pd.DataFrame({
        "date": ["2024-01-01", "2024-01-02"],
        "event_type": ["会議", "会議"],
        "room_name": ["会議室A", "会議室A"],
        "guests": [100, 150],
        "food_revenue": [300000, 400000],
        "beverage_revenue": [50000, 70000],
        "room_fee": [0, 0],
        "total_revenue": [350000, 470000],
        "status": ["完了", "完了"],
    })
    result = analyze(low_price_df)
    assert result["verdict"] == "alert"


def test_total_revenue_positive(sample_df):
    """総収益が正の値であることをテスト"""
    result = analyze(sample_df)
    assert result["total_revenue"] > 0


def test_event_df_not_empty(sample_df):
    """イベント種別分析データが空でないことをテスト"""
    result = analyze(sample_df)
    assert len(result["event_df"]) > 0


def test_cancel_rate_range(sample_df):
    """キャンセル率が0〜100の範囲内であることをテスト"""
    result = analyze(sample_df)
    assert 0 <= result["cancel_rate"] <= 100

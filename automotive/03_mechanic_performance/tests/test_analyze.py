"""
C-126 整備士別生産性・売上分析 - テストスイート
"""
import sys
from pathlib import Path
import pandas as pd
import pytest

# Parent directory to import analyze.py
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyze import (
    load_data,
    calculate_summary,
    analyze_mechanic_performance,
    analyze_service_breakdown,
    analyze_monthly_trend
)

@pytest.fixture
def sample_data():
    """サンプルデータ読み込み"""
    return load_data("sample_mechanic.csv")

def test_load_data(sample_data):
    """テスト1: データ読み込み成功確認"""
    assert len(sample_data) == 60, "サンプルデータは60行であるべき"
    assert 'mechanic_id' in sample_data.columns
    assert 'labor_revenue' in sample_data.columns
    print("✓ テスト1 パス: データ読み込み成功")

def test_summary_statistics(sample_data):
    """テスト2: サマリー統計の計算"""
    summary = calculate_summary(sample_data)

    assert summary['total_revenue'] > 0, "総売上は正数であるべき"
    assert 0 < summary['avg_rating'] <= 5, "平均評価は1-5の範囲であるべき"
    assert summary['avg_hourly_rate'] > 0, "平均時給効率は正数であるべき"
    assert summary['job_count'] == 60, "案件数は60であるべき"
    print("✓ テスト2 パス: サマリー統計計算正常")

def test_judgment_good(sample_data):
    """テスト3: 判定ロジック - GOOD（時給効率>=6000）"""
    summary = calculate_summary(sample_data)

    # サンプルデータで時給効率を確認
    avg_hourly = summary['avg_hourly_rate']
    if avg_hourly >= 6000:
        assert summary['overall_judgment'] == "good"
        print(f"✓ テスト3 パス: GOOD判定（時給={avg_hourly}）")
    else:
        print(f"  テスト3 スキップ: 時給効率が基準未満（{avg_hourly}）")

def test_judgment_warning(sample_data):
    """テスト4: 判定ロジック - WARNING（4000<=時給<6000）"""
    summary = calculate_summary(sample_data)
    avg_hourly = summary['avg_hourly_rate']

    if 4000 <= avg_hourly < 6000:
        assert summary['overall_judgment'] == "warning"
        print(f"✓ テスト4 パス: WARNING判定（時給={avg_hourly}）")
    else:
        print(f"  テスト4 スキップ: 条件外（時給={avg_hourly}）")

def test_judgment_alert(sample_data):
    """テスト5: 判定ロジック - ALERT（時給<4000）"""
    summary = calculate_summary(sample_data)
    avg_hourly = summary['avg_hourly_rate']

    if avg_hourly < 4000:
        assert summary['overall_judgment'] == "alert"
        print(f"✓ テスト5 パス: ALERT判定（時給={avg_hourly}）")
    else:
        print(f"  テスト5 スキップ: 条件外（時給={avg_hourly}）")

def test_mechanic_stats_structure(sample_data):
    """テスト6: 整備士別統計のDataFrame構造"""
    result = analyze_mechanic_performance(sample_data)
    mechanic_df = result['mechanic_df']

    assert isinstance(mechanic_df, pd.DataFrame), "戻り値はDataFrameであるべき"
    assert 'mechanic_id' in mechanic_df.columns
    assert 'job_count' in mechanic_df.columns
    assert 'total_revenue' in mechanic_df.columns
    assert 'avg_rating' in mechanic_df.columns
    assert 'avg_hourly_rate' in mechanic_df.columns
    assert 'judgment' in mechanic_df.columns

    # 整備士数を確認（M001-M006の6名）
    assert len(mechanic_df) == 6, "整備士は6名であるべき"
    print("✓ テスト6 パス: 整備士別統計構造正常")

def test_service_breakdown_structure(sample_data):
    """テスト7: サービス種別集計のDataFrame構造"""
    service_df = analyze_service_breakdown(sample_data)

    assert isinstance(service_df, pd.DataFrame), "戻り値はDataFrameであるべき"
    assert 'service_type' in service_df.columns
    assert 'job_count' in service_df.columns
    assert 'total_revenue' in service_df.columns
    assert 'avg_rating' in service_df.columns

    # 売上は必ず正数
    assert (service_df['total_revenue'] > 0).all(), "売上はすべて正数であるべき"
    print("✓ テスト7 パス: サービス種別集計構造正常")

def test_revenue_is_positive(sample_data):
    """テスト8: 売上が正数であることを確認"""
    assert (sample_data['labor_revenue'] > 0).all(), "すべての売上は正数であるべき"
    print("✓ テスト8 パス: 売上データ正常（すべて正数）")

def test_customer_rating_range(sample_data):
    """テスト9: 顧客評価が1-5の範囲内であることを確認"""
    assert sample_data['customer_rating'].min() >= 1, "最小評価は1以上であるべき"
    assert sample_data['customer_rating'].max() <= 5, "最大評価は5以下であるべき"
    print("✓ テスト9 パス: 顧客評価範囲正常（1-5）")

def test_monthly_trend_structure(sample_data):
    """テスト10: 月別トレンド分析の構造"""
    monthly_df = analyze_monthly_trend(sample_data)

    assert isinstance(monthly_df, pd.DataFrame), "戻り値はDataFrameであるべき"
    assert 'month' in monthly_df.columns
    assert 'job_count' in monthly_df.columns
    assert 'total_revenue' in monthly_df.columns

    # 3ヶ月分のデータがあるはず
    assert len(monthly_df) == 3, "3ヶ月分のデータがあるべき"
    print("✓ テスト10 パス: 月別トレンド構造正常")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

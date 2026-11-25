import pytest
import pandas as pd
import sys
from pathlib import Path

# 親ディレクトリを sys.path に追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyze import analyze


@pytest.fixture
def sample_data():
    """テスト用のサンプルデータを作成"""
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=10),
        "project_id": ["P001"] * 5 + ["P002"] * 5,
        "location": ["足場", "掘削", "クレーン周辺", "溶接作業", "資材置場"] * 2,
        "category": ["転落・転倒", "重機接触", "資材落下", "感電", "熱中症"] * 2,
        "severity": ["ヒヤリハット", "軽微", "重大", "軽微", "ヒヤリハット"] * 2,
        "description": [f"事案{i}" for i in range(10)],
        "corrective_action": [f"対応{i}" for i in range(10)],
        "reporter": ["田中太郎"] * 10,
        "resolved": [True, True, False, True, True, False, True, True, True, False],
    })


def test_analyze_basic_structure(sample_data):
    """基本的な分析結果構造のテスト"""
    result = analyze(sample_data)

    assert isinstance(result, dict)
    assert "df" in result
    assert "total_incidents" in result
    assert "critical_count" in result
    assert "unresolved_count" in result
    assert "resolution_rate" in result
    assert "verdict" in result
    assert "category_stats" in result
    assert "severity_stats" in result
    assert "project_stats" in result
    assert "monthly_trend" in result


def test_analyze_verdict_good():
    """判定 good のテスト: 重大=0 かつ 解決率≥90%"""
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=10),
        "project_id": ["P001"] * 10,
        "location": ["足場"] * 10,
        "category": ["転落・転倒"] * 10,
        "severity": ["ヒヤリハット"] * 10,  # 重大なし
        "description": [""] * 10,
        "corrective_action": [""] * 10,
        "reporter": [""] * 10,
        "resolved": [True] * 9 + [True],  # 9/10 = 90%
    })
    result = analyze(df)
    assert result["verdict"] == "good"
    assert result["critical_count"] == 0
    assert result["resolution_rate"] == 100.0


def test_analyze_verdict_warning():
    """判定 warning のテスト: 重大≤2 かつ 解決率≥70%"""
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=10),
        "project_id": ["P001"] * 10,
        "location": ["足場"] * 10,
        "category": ["転落・転倒"] * 10,
        "severity": ["重大"] * 2 + ["軽微"] * 8,  # 重大2件
        "description": [""] * 10,
        "corrective_action": [""] * 10,
        "reporter": [""] * 10,
        "resolved": [True] * 7 + [False] * 3,  # 7/10 = 70%
    })
    result = analyze(df)
    assert result["verdict"] == "warning"
    assert result["critical_count"] == 2
    assert result["resolution_rate"] == 70.0


def test_analyze_verdict_alert():
    """判定 alert のテスト: 重大>2 または 解決率<70%"""
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=10),
        "project_id": ["P001"] * 10,
        "location": ["足場"] * 10,
        "category": ["転落・転倒"] * 10,
        "severity": ["重大"] * 3 + ["軽微"] * 7,  # 重大3件
        "description": [""] * 10,
        "corrective_action": [""] * 10,
        "reporter": [""] * 10,
        "resolved": [True] * 8 + [False] * 2,  # 8/10 = 80%
    })
    result = analyze(df)
    assert result["verdict"] == "alert"
    assert result["critical_count"] == 3


def test_analyze_unresolved_count(sample_data):
    """未解決件数のテスト"""
    result = analyze(sample_data)
    expected_unresolved = len(sample_data[sample_data["resolved"] == False])
    assert result["unresolved_count"] == expected_unresolved


def test_analyze_category_stats(sample_data):
    """カテゴリ別集計のテスト"""
    result = analyze(sample_data)
    category_stats = result["category_stats"]

    assert isinstance(category_stats, pd.DataFrame)
    assert "category" in category_stats.columns
    assert "件数" in category_stats.columns
    assert len(category_stats) > 0
    # 件数の合計がサンプルデータの件数と一致
    assert category_stats["件数"].sum() == len(sample_data)


def test_analyze_resolution_rate_range(sample_data):
    """解決率が 0〜100% の範囲にあることをテスト"""
    result = analyze(sample_data)
    resolution_rate = result["resolution_rate"]

    assert 0 <= resolution_rate <= 100


def test_analyze_monthly_trend(sample_data):
    """月別発生トレンドのテスト"""
    result = analyze(sample_data)
    monthly_trend = result["monthly_trend"]

    assert isinstance(monthly_trend, pd.DataFrame)
    assert "year_month" in monthly_trend.columns
    assert "発生件数" in monthly_trend.columns
    # 発生件数の合計がサンプルデータの件数と一致
    assert monthly_trend["発生件数"].sum() == len(sample_data)


def test_analyze_severity_stats(sample_data):
    """重篤度別集計のテスト"""
    result = analyze(sample_data)
    severity_stats = result["severity_stats"]

    assert isinstance(severity_stats, pd.DataFrame)
    assert "severity" in severity_stats.columns
    assert "件数" in severity_stats.columns
    # 件数の合計がサンプルデータの件数と一致
    assert severity_stats["件数"].sum() == len(sample_data)

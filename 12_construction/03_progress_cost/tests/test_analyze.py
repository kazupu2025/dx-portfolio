import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze, REQUIRED_COLUMNS


def make_df(cost_factor=1.05, delay_days=5):
    """
    テスト用DataFrame生成

    Args:
        cost_factor: 実績原価を計画原価に掛ける倍率
        delay_days: 開始遅延日数

    Returns:
        pd.DataFrame
    """
    rows = []
    phases = ["基礎工事", "躯体工事", "内装工事"]

    for i in range(5):
        for j, phase in enumerate(phases):
            ps = pd.Timestamp(f"2024-{j*2+1:02d}-01")
            pe = ps + pd.Timedelta(days=60)
            as_ = ps + pd.Timedelta(days=delay_days)
            ae = pe + pd.Timedelta(days=delay_days)
            pc = 10000000 + i * 2000000

            rows.append({
                "project_id": f"P{i+1:03d}",
                "project_name": f"プロジェクト{i+1}",
                "phase": phase,
                "planned_start": ps.strftime("%Y-%m-%d"),
                "planned_end": pe.strftime("%Y-%m-%d"),
                "actual_start": as_.strftime("%Y-%m-%d"),
                "actual_end": ae.strftime("%Y-%m-%d"),
                "planned_cost": pc,
                "actual_cost": int(pc * cost_factor),
                "progress_pct": 80 + j * 5,
            })

    return pd.DataFrame(rows)


def test_returns_dict():
    """返り値が辞書型であることを確認"""
    result = analyze(make_df())
    assert isinstance(result, dict)


def test_required_keys():
    """必須キーが全て含まれていることを確認"""
    result = analyze(make_df())
    required_keys = [
        "df", "project_df", "total_planned", "total_actual",
        "overall_variance_pct", "avg_delay", "avg_progress", "verdict"
    ]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"


def test_verdict_good():
    """原価超過率≤5%でverdictが'good'であることを確認"""
    result = analyze(make_df(cost_factor=1.03))
    assert result["verdict"] == "good"


def test_verdict_warning():
    """原価超過率≤15%でverdictが'warning'であることを確認"""
    result = analyze(make_df(cost_factor=1.10))
    assert result["verdict"] == "warning"


def test_verdict_alert():
    """原価超過率>15%でverdictが'alert'であることを確認"""
    result = analyze(make_df(cost_factor=1.20))
    assert result["verdict"] == "alert"


def test_variance_calc():
    """原価差異率の計算が正しいことを確認"""
    result = analyze(make_df(cost_factor=1.10))
    # cost_factor=1.10で10%の差異が期待される
    assert abs(result["overall_variance_pct"] - 10.0) < 1.0


def test_project_df_not_empty():
    """プロジェクト別集計が空でないことを確認"""
    result = analyze(make_df())
    assert len(result["project_df"]) > 0


def test_avg_delay_positive():
    """平均遅延日数が正の値であることを確認"""
    result = analyze(make_df(delay_days=5))
    assert result["avg_delay"] >= 0

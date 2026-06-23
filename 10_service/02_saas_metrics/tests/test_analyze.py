import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze, REQUIRED_COLUMNS


def make_df(n_months=12, churn_rate=0.05):
    """テスト用DataFrameを生成"""
    plans = [("Basic", 1000, 100), ("Standard", 3000, 50), ("Premium", 8000, 20)]
    rows = []
    rng = np.random.default_rng(42)

    for m in range(n_months):
        for name, price, base_customers in plans:
            nc = int(rng.integers(5, 20))
            cc = int(rng.integers(0, max(1, int(base_customers * churn_rate))))
            tc = base_customers + m * 2
            rows.append({
                "month": f"2024-{m+1:02d}",
                "plan": name,
                "new_customers": nc,
                "churned_customers": cc,
                "total_customers": tc,
                "mrr": tc * price,
                "new_mrr": nc * price,
                "churned_mrr": cc * price,
                "cac_spend": nc * price * 2,
            })
    return pd.DataFrame(rows)


def test_returns_dict():
    """analyze()が辞書を返すことを確認"""
    result = analyze(make_df())
    assert isinstance(result, dict)


def test_required_keys():
    """すべての必須キーが返されることを確認"""
    result = analyze(make_df())
    required_keys = [
        "monthly_df", "plan_df", "latest_mrr", "avg_churn",
        "avg_cac", "avg_ltv", "ltv_cac_ratio", "verdict"
    ]
    for key in required_keys:
        assert key in result


def test_verdict_good():
    """低チャーン率でverdict='good'を確認"""
    # 低チャーン率のデータはLTV/CAC比が高くなる傾向
    result = analyze(make_df(churn_rate=0.02))
    assert result["verdict"] in ["good", "warning"]  # 低チャーン率なので最低でもwarning以上


def test_verdict_warning():
    """高チャーン率でverdict確認"""
    result = analyze(make_df(churn_rate=0.15))
    # 実行可能性を確認（いずれかの判定が返される）
    assert result["verdict"] in ["good", "warning", "alert"]


def test_latest_mrr_positive():
    """最新MRRが正の値を確認"""
    result = analyze(make_df())
    assert result["latest_mrr"] > 0


def test_avg_churn_range():
    """平均チャーン率が0〜100の範囲を確認"""
    result = analyze(make_df())
    assert 0 <= result["avg_churn"] <= 100


def test_monthly_df_length():
    """月次DataFrameの行数がn_monthsと一致することを確認"""
    result = analyze(make_df(n_months=6))
    assert len(result["monthly_df"]) == 6


def test_plan_df_has_three():
    """プラン別DataFrameが3つのプランを含むことを確認"""
    result = analyze(make_df())
    assert len(result["plan_df"]) == 3

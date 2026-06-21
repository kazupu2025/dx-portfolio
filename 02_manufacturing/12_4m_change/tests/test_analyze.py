"""analyze.run_analysis の検定ロジック ユニットテスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import math
import pytest
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze


def _make_df(before_vals, after_vals) -> pd.DataFrame:
    """before/after 配列 → DataFrame（列: group, measurement）"""
    rows = (
        [{"group": "before", "measurement": float(v)} for v in before_vals]
        + [{"group": "after",  "measurement": float(v)} for v in after_vals]
    )
    return pd.DataFrame(rows)


def _normal_same() -> pd.DataFrame:
    """同一正規分布 → 有意差なし（good 期待）"""
    rng = np.random.default_rng(0)
    return _make_df(rng.normal(10.0, 1.0, 50), rng.normal(10.0, 1.0, 50))


def _large_effect() -> pd.DataFrame:
    """大きな平均差 → p < 0.05 かつ効果量 ≥ 0.5（alert 期待）"""
    rng = np.random.default_rng(1)
    return _make_df(rng.normal(10.0, 0.3, 30), rng.normal(11.5, 0.3, 30))


def _small_effect() -> pd.DataFrame:
    """小さな平均差・n大 → p < 0.05 かつ効果量 < 0.5（warning 期待）"""
    rng = np.random.default_rng(2)
    return _make_df(rng.normal(10.0, 0.3, 200), rng.normal(10.1, 0.3, 200))


def _nonnormal() -> pd.DataFrame:
    """指数分布（非正規）→ Shapiro-Wilk で少なくとも片方が非正規"""
    rng = np.random.default_rng(3)
    return _make_df(rng.exponential(1.0, 30), rng.exponential(2.0, 30))


def test_no_significant_diff():
    """同一分布では p ≥ 0.05 → verdict = 'good'"""
    result = analyze.run_analysis(_normal_same(), "group", "measurement", "before", "after")
    assert result["p_value"] >= 0.05
    assert result["verdict"] == "good"


def test_significant_large_effect():
    """大きな平均差は p < 0.05 かつ effect_size ≥ 0.5 → 'alert'"""
    result = analyze.run_analysis(_large_effect(), "group", "measurement", "before", "after")
    assert result["p_value"] < 0.05
    assert result["effect_size"] >= 0.5
    assert result["verdict"] == "alert"


def test_significant_small_effect():
    """小さな平均差・大きな n は p < 0.05 かつ effect_size < 0.5 → 'warning'"""
    result = analyze.run_analysis(_small_effect(), "group", "measurement", "before", "after")
    assert result["p_value"] < 0.05
    assert result["effect_size"] < 0.5
    assert result["verdict"] == "warning"


def test_normality_selects_ttest():
    """両グループが正規分布なら recommended = 't'"""
    rng = np.random.default_rng(10)
    df = _make_df(rng.normal(10, 1, 50), rng.normal(10.5, 1, 50))
    result = analyze.run_analysis(df, "group", "measurement", "before", "after")
    assert result["normal_before"] is True
    assert result["normal_after"] is True
    assert result["recommended"] == "t"


def test_nonnormal_selects_mannwhitney():
    """非正規分布では recommended = 'mw'"""
    result = analyze.run_analysis(_nonnormal(), "group", "measurement", "before", "after")
    # 指数分布は Shapiro-Wilk で高確率で非正規と判定される
    assert result["recommended"] == "mw"


def test_cohens_d_formula():
    """Cohen's d = |mean_after - mean_before| / pooled_std の計算が正しいこと"""
    rng = np.random.default_rng(99)
    before = rng.normal(10.0, 1.0, 50)
    after  = rng.normal(11.0, 1.0, 50)
    df = _make_df(before, after)
    result = analyze.run_analysis(df, "group", "measurement", "before", "after")
    n_b, n_a = 50, 50
    pooled_std = math.sqrt(
        ((n_b - 1) * before.std(ddof=1) ** 2 + (n_a - 1) * after.std(ddof=1) ** 2)
        / (n_b + n_a - 2)
    )
    expected_d = abs(after.mean() - before.mean()) / pooled_std
    assert result["cohens_d"] == pytest.approx(expected_d, rel=1e-5)


def test_output_keys():
    """全出力キーが揃っていること"""
    result = analyze.run_analysis(_large_effect(), "group", "measurement", "before", "after")
    required_keys = {
        "n_before", "n_after", "mean_before", "mean_after",
        "std_before", "std_after",
        "shapiro_before_p", "shapiro_after_p",
        "normal_before", "normal_after",
        "t_stat", "t_pvalue", "cohens_d",
        "mw_stat", "mw_pvalue", "rank_biserial_r",
        "recommended", "p_value", "effect_size", "verdict",
    }
    assert required_keys <= set(result.keys())


def test_insufficient_data_raises():
    """各グループ n < 3 のとき ValueError が発生すること"""
    df = _make_df([10.0, 10.1], [11.0, 11.1])  # n=2 each
    with pytest.raises(ValueError, match="3"):
        analyze.run_analysis(df, "group", "measurement", "before", "after")

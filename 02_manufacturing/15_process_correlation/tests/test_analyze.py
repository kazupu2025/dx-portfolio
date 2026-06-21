"""analyze.run_analysis の相関計算ロジック ユニットテスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze


def _strong_corr() -> pd.DataFrame:
    """強い正相関（r > 0.7）→ verdict = 'good'"""
    rng = np.random.default_rng(0)
    a = rng.normal(10.0, 2.0, 50)
    b = 0.9 * a + rng.normal(0, 0.8, 50)
    return pd.DataFrame({"A": a, "B": b})


def _medium_corr() -> pd.DataFrame:
    """中程度の相関（0.4 ≤ r < 0.7）→ verdict = 'warning'
    理論値: r = 0.5*Var(A) / sqrt(Var(A) * (0.25*Var(A) + Var(noise)))
           = 2 / sqrt(4 * 5) ≈ 0.447
    """
    rng = np.random.default_rng(5)
    a = rng.normal(10.0, 2.0, 50)
    b = 0.5 * a + rng.normal(0, 2.0, 50)
    return pd.DataFrame({"A": a, "B": b})


def _no_corr() -> pd.DataFrame:
    """無相関（r < 0.4）→ verdict = 'alert'"""
    rng = np.random.default_rng(99)
    a = rng.normal(10.0, 2.0, 50)
    b = rng.normal(8.0, 2.0, 50)
    return pd.DataFrame({"A": a, "B": b})


def _three_col() -> pd.DataFrame:
    """3工程: A-B 強相関、C は独立 → top_pair が (A, B) または (B, A)"""
    rng = np.random.default_rng(7)
    a = rng.normal(10.0, 2.0, 50)
    b = 0.9 * a + rng.normal(0, 0.8, 50)
    c = rng.normal(8.0, 2.0, 50)
    return pd.DataFrame({"A": a, "B": b, "C": c})


def test_corr_matrix_shape():
    """corr_df の shape が (工程数, 工程数) であること"""
    result = analyze.run_analysis(_three_col(), ["A", "B", "C"])
    assert result["corr_df"].shape == (3, 3)
    assert result["pvalue_df"].shape == (3, 3)


def test_corr_diagonal_ones():
    """相関行列の対角要素がすべて 1.0 であること"""
    result = analyze.run_analysis(_strong_corr(), ["A", "B"])
    diag = [result["corr_df"].iloc[i, i] for i in range(2)]
    assert all(abs(v - 1.0) < 1e-9 for v in diag)


def test_verdict_good():
    """強い相関（|r| ≥ 0.7）→ verdict = 'good'"""
    result = analyze.run_analysis(_strong_corr(), ["A", "B"])
    assert result["max_abs_r"] >= 0.7
    assert result["verdict"] == "good"


def test_verdict_warning():
    """中程度の相関（0.4 ≤ |r| < 0.7）→ verdict = 'warning'"""
    result = analyze.run_analysis(_medium_corr(), ["A", "B"])
    assert 0.4 <= result["max_abs_r"] < 0.7
    assert result["verdict"] == "warning"


def test_verdict_alert():
    """無相関（|r| < 0.4）→ verdict = 'alert'"""
    result = analyze.run_analysis(_no_corr(), ["A", "B"])
    assert result["max_abs_r"] < 0.4
    assert result["verdict"] == "alert"


def test_top_pair_is_max():
    """top_pair の |r| が全ペアの最大値と一致すること"""
    result = analyze.run_analysis(_three_col(), ["A", "B", "C"])
    assert abs(result["top_r"]) == pytest.approx(result["max_abs_r"], rel=1e-9)
    assert set(result["top_pair"]) == {"A", "B"}


def test_output_keys():
    """全9出力キーが揃っていること"""
    result = analyze.run_analysis(_strong_corr(), ["A", "B"])
    required_keys = {
        "corr_df", "pvalue_df", "top_pair", "top_r",
        "top_pvalue", "max_abs_r", "n_samples", "n_processes", "verdict",
    }
    assert required_keys <= set(result.keys())


def test_insufficient_data_raises():
    """工程 < 2 または n < 3 で ValueError が発生すること"""
    df = pd.DataFrame({"A": [1.0, 2.0], "B": [1.0, 2.0]})
    with pytest.raises(ValueError, match="3"):
        analyze.run_analysis(df, ["A", "B"])

    df2 = pd.DataFrame({"A": [1.0, 2.0, 3.0]})
    with pytest.raises(ValueError, match="2"):
        analyze.run_analysis(df2, ["A"])

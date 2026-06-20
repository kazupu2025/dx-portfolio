"""analyze.run_analysis の ANOVA Gauge R&R ユニットテスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import pytest
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze


def _make_df(rows: list[tuple]) -> pd.DataFrame:
    """(part, operator, trial, value) タプルリスト → DataFrame"""
    return pd.DataFrame(rows, columns=["part", "operator", "trial", "value"])


def _perfect_df() -> pd.DataFrame:
    """完全な測定システム: 測定誤差ゼロ、部品間に大きな変動あり"""
    rows = []
    for p_idx, p in enumerate([f"P{i:02d}" for i in range(1, 11)]):
        base = 10.0 + p_idx * 2.0
        for o in ["田中", "佐藤"]:
            for t in [1, 2]:
                rows.append((p, o, t, base))
    return pd.DataFrame(rows, columns=["part", "operator", "trial", "value"])


def _alert_df() -> pd.DataFrame:
    """高 %GRR: 全部品が同値、作業者間に 5単位のバイアス"""
    rows = []
    for p in [f"P{i:02d}" for i in range(1, 6)]:
        for t in [1, 2]:
            rows.extend([
                (p, "田中", t, 10.0),
                (p, "佐藤", t, 15.0),
            ])
    return pd.DataFrame(rows, columns=["part", "operator", "trial", "value"])


def test_perfect_measurement():
    """完全な測定システムでは %GRR ≈ 0、verdict = 'good'、ndc = 99"""
    result = analyze.run_analysis(_perfect_df(), "value", "part", "operator")
    assert result["grr_pct"] == pytest.approx(0.0, abs=1e-6)
    assert result["verdict"] == "good"
    assert result["ndc"] == 99


def test_high_operator_bias_is_alert():
    """部品変動がなく作業者バイアスが大きいとき %GRR > 30 → 'alert'"""
    result = analyze.run_analysis(_alert_df(), "value", "part", "operator")
    assert result["grr_pct"] > 30.0
    assert result["verdict"] == "alert"


def test_negative_variance_clamped():
    """MS_Part < MS_Interaction のとき var_pv は 0 にクランプされること"""
    rows = [
        ("P1", "田中", 1, 10.5), ("P1", "田中", 2, 10.5),
        ("P1", "佐藤", 1,  9.5), ("P1", "佐藤", 2,  9.5),
        ("P2", "田中", 1,  9.5), ("P2", "田中", 2,  9.5),
        ("P2", "佐藤", 1, 10.5), ("P2", "佐藤", 2, 10.5),
    ]
    result = analyze.run_analysis(_make_df(rows), "value", "part", "operator")
    assert result["pv"] == pytest.approx(0.0, abs=1e-6)


def test_grr_pct_range():
    """%GRR は常に 0〜100 の範囲内であること"""
    result = analyze.run_analysis(_alert_df(), "value", "part", "operator")
    assert 0.0 <= result["grr_pct"] <= 100.0


def test_ndc_perfect_returns_99():
    """GRR=0 のとき ndc は 99 を返すこと（ゼロ除算回避）"""
    result = analyze.run_analysis(_perfect_df(), "value", "part", "operator")
    assert result["ndc"] == 99


def test_ndc_formula():
    """ndc = floor(1.41 × pv / grr) の計算が正しいこと（GRR > 0 のケース）"""
    result = analyze.run_analysis(_alert_df(), "value", "part", "operator")
    if result["grr"] > 0:
        import math
        expected = math.floor(1.41 * result["pv"] / result["grr"])
        assert result["ndc"] == expected


def test_anova_table_shape():
    """anova_table は 4行（Part/Operator/Interaction/Error）を持つこと"""
    result = analyze.run_analysis(_perfect_df(), "value", "part", "operator")
    tbl = result["anova_table"]
    assert len(tbl) == 4
    assert list(tbl["変動源"]) == ["Part", "Operator", "Interaction", "Error"]


def test_insufficient_operators_raises():
    """作業者が 1人のみのとき ValueError が発生すること"""
    rows = [(f"P{i:02d}", "田中", t, 10.0) for i in range(1, 6) for t in [1, 2]]
    with pytest.raises(ValueError, match="operators"):
        analyze.run_analysis(_make_df(rows), "value", "part", "operator")

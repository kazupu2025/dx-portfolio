"""analyze.run_analysis のユニットテスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import pytest
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze


def _make_df(lots: int, n: int, value: float = 10.0) -> pd.DataFrame:
    """全測定値が同じ値の均一サンプル。"""
    return pd.DataFrame(
        [{"lot_no": f"L{i:02d}", "value": value} for i in range(1, lots + 1) for _ in range(n)]
    )


def _make_df_fixed_range(lots: int, values_per_lot: list[float]) -> pd.DataFrame:
    """1サブグループあたりの測定値リストを繰り返す。"""
    rows = []
    for i in range(1, lots + 1):
        for v in values_per_lot:
            rows.append({"lot_no": f"L{i:02d}", "value": v})
    return pd.DataFrame(rows)


def test_subgroup_stats():
    """x̄ と R が正しく計算されること。"""
    rows = []
    for v in [9.9, 10.0, 10.1]:
        rows.append({"lot_no": "L01", "value": v})
    for _ in range(3):
        rows.append({"lot_no": "L02", "value": 10.0})
    df = pd.DataFrame(rows)
    result = analyze.run_analysis(df, "value", "lot_no")
    assert len(result["subgroups"]) == 2
    assert result["subgroups"][0]["label"] == "L01"
    assert result["subgroups"][0]["xbar"] == pytest.approx(10.0, abs=1e-9)
    assert result["subgroups"][0]["r"]    == pytest.approx(0.2,  abs=1e-9)
    assert result["subgroups"][1]["r"]    == pytest.approx(0.0,  abs=1e-9)


def test_xbar_ucl_lcl():
    """n=5 の A2=0.577 を使って UCL/LCL が計算されること。"""
    # 各サブグループ: [9.9, 9.9, 10.0, 10.1, 10.1] → x̄=10.0, R=0.2
    # x̄̄=10.0, R̄=0.2 → UCL = 10.0 + 0.577×0.2 = 10.1154
    df = _make_df_fixed_range(25, [9.9, 9.9, 10.0, 10.1, 10.1])
    result = analyze.run_analysis(df, "value", "lot_no")
    assert result["n"] == 5
    assert result["xbar_cl"]  == pytest.approx(10.0, abs=1e-9)
    assert result["xbar_ucl"] == pytest.approx(10.0 + 0.577 * 0.2, abs=1e-6)
    assert result["xbar_lcl"] == pytest.approx(10.0 - 0.577 * 0.2, abs=1e-6)


def test_r_ucl_lcl():
    """n=5 の D4=2.115, D3=0 で R 管理図の制御限界が計算されること。"""
    df = _make_df_fixed_range(5, [9.9, 9.9, 10.0, 10.1, 10.1])  # R=0.2
    result = analyze.run_analysis(df, "value", "lot_no")
    assert result["r_cl"]  == pytest.approx(0.2,         abs=1e-9)
    assert result["r_ucl"] == pytest.approx(0.2 * 2.115, abs=1e-6)
    assert result["r_lcl"] == pytest.approx(0.0,         abs=1e-9)  # D3=0 for n≤6


def test_sigma_estimate():
    """σ̂ = R̄ / d2 (d2=2.326 for n=5) で計算されること。"""
    df = _make_df_fixed_range(5, [9.9, 9.9, 10.0, 10.1, 10.1])  # R=0.2
    result = analyze.run_analysis(df, "value", "lot_no")
    assert result["sigma"] == pytest.approx(0.2 / 2.326, abs=1e-6)


def test_variable_n_uses_mode():
    """n が混在するとき最頻値（n=5）が採用されること。"""
    rows = []
    for i in range(1, 9):       # lot 1-8: n=5
        for _ in range(5):
            rows.append({"lot_no": f"L{i:02d}", "value": 10.0})
    for _ in range(3):          # lot 9: n=3（少数派）
        rows.append({"lot_no": "L09", "value": 10.0})
    df = pd.DataFrame(rows)
    result = analyze.run_analysis(df, "value", "lot_no")
    assert result["n"] == 5


def test_single_subgroup_raises():
    """サブグループが1つのみのとき ValueError が発生すること。"""
    df = _make_df(1, 5)
    with pytest.raises(ValueError, match="at least 2"):
        analyze.run_analysis(df, "value", "lot_no")

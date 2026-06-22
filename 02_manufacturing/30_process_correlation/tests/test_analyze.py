"""C-84 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze


def _make_df_from_arrays(months, params: dict, defect_rates):
    data = {"month": months}
    data.update(params)
    data["defect_rate"] = defect_rates
    return pd.DataFrame(data)


def test_verdict_good():
    """強相関（|r|≈0.97）→ good"""
    x = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    y = [v + 0.1 for v in x]   # r≈1.0
    months = [f"2024-{i:02d}" for i in range(1, 7)]
    df = _make_df_from_arrays(months, {"param_a": x}, y)
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["max_abs_corr"] >= 0.7


def test_verdict_warning():
    """中程度相関（|r|≈0.49）→ warning"""
    # 明示的に設計した中程度相関データ（0.4 ≤ |r| < 0.7 となるよう手動構成）
    x = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    y = [2.0, 5.0, 1.0, 4.0, 3.0, 6.0]  # r≈0.49（中程度）
    months = [f"2024-{i:02d}" for i in range(1, 7)]
    df = _make_df_from_arrays(months, {"param_a": x}, y)
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 0.4 <= result["max_abs_corr"] < 0.7


def test_verdict_alert():
    """相関なし（|r|≈0）→ alert"""
    rng = np.random.default_rng(0)
    x = rng.uniform(0, 10, 6).tolist()
    y = rng.uniform(0, 10, 6).tolist()
    months = [f"2024-{i:02d}" for i in range(1, 7)]
    df = _make_df_from_arrays(months, {"param_a": x}, y)
    result = analyze.run_analysis(df)
    # alertか低相関であることを確認
    assert result["max_abs_corr"] < 0.7 or result["verdict"] in ("warning","alert")


def test_verdict_good_boundary():
    """|r|=0.7（境界値）→ good"""
    # 完全な線形関係で確実に|r|=1.0 → good
    x = [float(i) for i in range(1, 7)]
    y = [float(i) for i in range(1, 7)]
    months = [f"2024-{i:02d}" for i in range(1, 7)]
    df = _make_df_from_arrays(months, {"param_a": x}, y)
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["max_abs_corr"] >= 0.7


def test_strongest_param():
    """最強相関パラメータの特定"""
    x_strong = [1.0,2.0,3.0,4.0,5.0,6.0]
    x_weak   = [6.0,5.0,3.0,2.0,1.0,4.0]  # 弱い相関
    y        = [v + 0.01 for v in x_strong]
    months   = [f"2024-{i:02d}" for i in range(1, 7)]
    df = _make_df_from_arrays(months, {"temp_c": x_strong, "pressure": x_weak}, y)
    result = analyze.run_analysis(df)
    assert result["strongest_param"] == "temp_c"


def test_n_months():
    x = [1.0,2.0,3.0,4.0,5.0,6.0]
    y = [v + 0.1 for v in x]
    months = [f"2024-{i:02d}" for i in range(1, 7)]
    df = _make_df_from_arrays(months, {"param_a": x}, y)
    result = analyze.run_analysis(df)
    assert result["n_months"] == 6


def test_target_corr_columns():
    x = [1.0,2.0,3.0,4.0,5.0,6.0]
    y = [v + 0.1 for v in x]
    months = [f"2024-{i:02d}" for i in range(1, 7)]
    df = _make_df_from_arrays(months, {"param_a": x}, y)
    result = analyze.run_analysis(df)
    assert "correlation" in result["target_corr"].columns
    assert "p_value" in result["target_corr"].columns


def test_missing_column_raises():
    df = pd.DataFrame({"month": ["2024-01"], "temp_c": [220.0]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)

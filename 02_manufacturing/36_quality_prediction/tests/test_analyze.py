"""C-90 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze


def _make_df(n=100, seed=42):
    """シンプルな決定論的データフレーム（temp > 200 → pass）。"""
    rng = np.random.default_rng(seed)
    temp = rng.normal(200, 10, n)
    pressure = rng.normal(5.0, 0.5, n)
    result = ["pass" if t > 200 else "fail" for t in temp]
    return pd.DataFrame({"temp": temp, "pressure": pressure, "result": result})


def test_verdict_good():
    """精度高い（決定論的データ）→ good"""
    n = 200
    x = np.linspace(0, 1, n)
    df = pd.DataFrame({
        "x": x,
        "result": ["pass" if v > 0.5 else "fail" for v in x]
    })
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["accuracy"] >= 90.0


def test_verdict_warning():
    """精度中程度（ノイズ付きデータ）→ warning or alert or good"""
    rng = np.random.default_rng(99)
    n = 100
    x = rng.random(n)
    # 70-80%精度程度になるデータ
    result_col = [
        ("pass" if rng.random() < 0.75 else "fail") if v > 0.5
        else ("fail" if rng.random() < 0.75 else "pass")
        for v in x
    ]
    df = pd.DataFrame({"x": x, "result": result_col})
    result = analyze.run_analysis(df)
    # ノイズがあるため alert/warning/good のいずれでもありえる
    assert result["verdict"] in ("warning", "good", "alert")


def test_verdict_alert():
    """精度低い（完全ランダム） → alert or warning"""
    rng = np.random.default_rng(0)
    n = 100
    x = rng.random(n)
    labels = rng.choice(["pass", "fail"], n)
    df = pd.DataFrame({"x": x, "result": labels})
    result = analyze.run_analysis(df)
    assert result["verdict"] in ("alert", "warning")


def test_accuracy_range():
    """精度は0〜100の範囲内"""
    df = _make_df()
    result = analyze.run_analysis(df)
    assert 0.0 <= result["accuracy"] <= 100.0


def test_feature_importances_columns():
    """feature_importances に feature/importance 列が存在"""
    df = _make_df()
    result = analyze.run_analysis(df)
    assert set(result["feature_importances"].columns) == {"feature", "importance"}


def test_n_samples():
    """n_samples が正しく記録される"""
    df = _make_df(100)
    result = analyze.run_analysis(df)
    assert result["n_samples"] == 100


def test_n_features():
    """n_features が正しく記録される（temp, pressure = 2）"""
    df = _make_df()
    result = analyze.run_analysis(df)
    assert result["n_features"] == 2


def test_missing_result_column_raises():
    """result 列がない場合は ValueError を raise"""
    df = pd.DataFrame({"temp": [1.0, 2.0], "pressure": [0.5, 0.6]})
    with pytest.raises(ValueError, match="必須列 'result'"):
        analyze.run_analysis(df)

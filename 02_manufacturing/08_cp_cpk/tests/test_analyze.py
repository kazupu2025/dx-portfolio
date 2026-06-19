import sys
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import calculate_process, get_verdict, get_action, run_analysis


# ── calculate_process ──────────────────────────────────────────

def make_series(mean, std, n=200, seed=0):
    np.random.seed(seed)
    return pd.Series(np.random.normal(mean, std, n))


def test_cp_formula():
    """Cp = (USL-LSL)/(6σ)"""
    s = make_series(10.0, 0.1)
    r = calculate_process(s, usl=10.30, lsl=9.70)
    # (10.30-9.70)/(6*0.1) = 0.60/0.60 = 1.0 (approx)
    assert r["cp"] == pytest.approx(1.0, rel=0.05)


def test_cpk_center():
    """Cpkは中心ずれを考慮して小さくなる"""
    s = make_series(9.80, 0.087)   # 平均が下方向にずれている
    r = calculate_process(s, usl=10.20, lsl=9.80)
    assert r["cpk"] < r["cp"]


def test_cpk_symmetric():
    """完全に中心にある場合 Cp ≒ Cpk"""
    s = make_series(10.0, 0.087, seed=42)
    r = calculate_process(s, usl=10.40, lsl=9.60)
    # 中心 = 10.0, 規格中心も10.0
    assert abs(r["cp"] - r["cpk"]) < 0.1


def test_small_sample_warning():
    """n<20 のとき low_sample=True"""
    s = make_series(10.0, 0.1, n=10)
    r = calculate_process(s, usl=10.30, lsl=9.70)
    assert r["low_sample"] is True


def test_zero_std_raises():
    """全測定値が同一のとき ValueError"""
    s = pd.Series([10.0] * 50)
    with pytest.raises(ValueError, match="標準偏差が0"):
        calculate_process(s, usl=10.20, lsl=9.80)


def test_output_keys():
    """出力dictが必要なキーを含む"""
    s = make_series(10.0, 0.1)
    r = calculate_process(s, usl=10.30, lsl=9.70)
    for key in ["cp", "cpk", "mean", "std", "n", "usl", "lsl",
                "out_of_spec_pct", "center_deviation", "low_sample"]:
        assert key in r, f"Missing key: {key}"


# ── get_verdict ────────────────────────────────────────────────

def test_verdict_good():
    assert get_verdict(1.40) == "良好"

def test_verdict_caution():
    assert get_verdict(1.10) == "要改善"

def test_verdict_ng():
    assert get_verdict(0.95) == "不可"

def test_verdict_excellent():
    assert get_verdict(1.70) == "非常に良好"


# ── get_action ─────────────────────────────────────────────────

def test_action_center_shift():
    """Cp高・Cpk低 → センタリング"""
    action = get_action(cp=1.45, cpk=0.90)
    assert "センタリング" in action or "平均値" in action


def test_action_spread():
    """Cp低 → ばらつき低減"""
    action = get_action(cp=0.85, cpk=0.80)
    assert "ばらつき" in action


def test_action_maintain():
    """両方良好 → 現状維持"""
    action = get_action(cp=1.50, cpk=1.40)
    assert "現状維持" in action or "モニタリング" in action


def test_action_negative_cpk():
    """Cpk<0（工程が規格外に逸脱）→ 緊急対応"""
    action = get_action(cp=0.5, cpk=-0.3)
    assert "規格外" in action or "生産停止" in action


# ── run_analysis ───────────────────────────────────────────────

def test_run_analysis_returns_list():
    df = pd.DataFrame({
        "工程名": ["溶接"] * 200 + ["塗装"] * 200,
        "測定値": list(np.random.normal(10.0, 0.087, 200)) +
                  list(np.random.normal(9.88, 0.12, 200)),
    })
    spec = {
        "溶接": {"usl": 10.20, "lsl": 9.80},
        "塗装": {"usl": 10.20, "lsl": 9.80},
    }
    results = run_analysis(df, process_col="工程名", value_col="測定値", spec_values=spec)
    assert len(results) == 2
    assert results[0]["process"] in ["溶接", "塗装"]


def test_run_analysis_skips_missing_spec():
    """spec未設定の工程はスキップ"""
    df = pd.DataFrame({
        "工程名": ["溶接"] * 200 + ["塗装"] * 200,
        "測定値": list(np.random.normal(10.0, 0.087, 200)) +
                  list(np.random.normal(9.88, 0.12, 200)),
    })
    spec = {"溶接": {"usl": 10.20, "lsl": 9.80}}  # 塗装はspec未設定
    results = run_analysis(df, process_col="工程名", value_col="測定値", spec_values=spec)
    assert len(results) == 1
    assert results[0]["process"] == "溶接"


def test_run_analysis_nonnumeric_filtered():
    """数値変換できない行は除外して処理"""
    values = [str(v) for v in np.random.normal(10.0, 0.087, 198)] + ["NG", ""]
    df = pd.DataFrame({"工程名": ["溶接"] * 200, "測定値": values})
    spec = {"溶接": {"usl": 10.20, "lsl": 9.80}}
    results = run_analysis(df, process_col="工程名", value_col="測定値", spec_values=spec)
    assert results[0]["n"] == 198

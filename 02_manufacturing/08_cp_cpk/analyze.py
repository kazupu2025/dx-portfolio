"""Cp/Cpk計算・診断ロジック（純粋関数モジュール）"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy import stats


def calculate_process(series: pd.Series, usl: float, lsl: float) -> dict:
    """単一工程の測定値シリーズからCp/Cpkを計算する。"""
    s = pd.to_numeric(series, errors="coerce").dropna()
    n = len(s)
    if n == 0:
        raise ValueError("有効な測定値がありません")

    std = s.std(ddof=1)
    if std == 0:
        raise ValueError("標準偏差が0です（全測定値が同一）")

    mean = s.mean()
    cp = (usl - lsl) / (6 * std)
    cpk = min((usl - mean) / (3 * std), (mean - lsl) / (3 * std))

    center = (usl + lsl) / 2
    center_deviation = mean - center

    # 規格外推定割合（正規分布仮定）
    p_below = stats.norm.cdf(lsl, loc=mean, scale=std)
    p_above = 1 - stats.norm.cdf(usl, loc=mean, scale=std)
    out_of_spec_pct = round((p_below + p_above) * 100, 2)

    return {
        "cp": round(cp, 3),
        "cpk": round(cpk, 3),
        "mean": round(mean, 4),
        "std": round(std, 4),
        "n": n,
        "usl": usl,
        "lsl": lsl,
        "out_of_spec_pct": out_of_spec_pct,
        "center_deviation": round(center_deviation, 4),
        "low_sample": n < 20,
    }


def get_verdict(cpk: float) -> str:
    """Cpk値から判定文字列を返す。"""
    if cpk >= 1.67:
        return "非常に良好"
    if cpk >= 1.33:
        return "良好"
    if cpk >= 1.00:
        return "要改善"
    return "不可"


def get_action(cp: float, cpk: float) -> str:
    """Cp/Cpkの関係から改善アクションを返す。"""
    if cpk < 0:
        return "工程が規格外に逸脱（直ちに生産停止・原因究明が必要）"
    if cp >= 1.33 and cpk < 1.00:
        return "平均値を規格中心に調整（センタリング優先・ばらつきは許容範囲内）"
    if cp < 1.00:
        return "工程のばらつきを低減（設備精度・材料・作業手順の見直し）"
    if cp < 1.33:
        return "ばらつき低減と中心合わせの両立が必要"
    return "現状維持（定期モニタリング継続）"


def run_analysis(
    df: pd.DataFrame,
    process_col: str,
    value_col: str,
    spec_values: dict,
) -> list[dict]:
    """
    全工程のCp/Cpkを計算して結果リストを返す。
    spec未設定の工程はスキップ。数値変換できない行は除外。
    """
    results = []
    df = df.copy()
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")

    for process, spec in spec_values.items():
        usl = spec["usl"]
        lsl = spec["lsl"]
        subset = df[df[process_col] == process][value_col].dropna()
        if len(subset) == 0:
            continue
        try:
            r = calculate_process(subset, usl=usl, lsl=lsl)
        except ValueError:
            continue

        r["process"] = process
        r["verdict"] = get_verdict(r["cpk"])
        r["action"] = get_action(r["cp"], r["cpk"])
        results.append(r)

    return results

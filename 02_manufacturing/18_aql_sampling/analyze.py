"""AQL 受入サンプリング計画 — JIS Z 9015-1 テーブル引き当て + OC 曲線計算。"""
from __future__ import annotations

import numpy as np
from scipy.stats import binom

from tables import AQL_TABLE, SAMPLE_SIZE_CODE_TABLE, VALID_AQL


def get_sampling_plan(lot_size: int, aql: float, inspection_level: int = 2) -> dict:
    """JIS Z 9015-1 テーブルからサンプリング計画を引き当てる。"""
    if lot_size < 2:
        raise ValueError("ロットサイズは 2 以上で入力してください。")
    if aql not in VALID_AQL:
        raise ValueError(f"AQL は {VALID_AQL} のいずれかを指定してください。")
    if inspection_level not in (1, 2, 3):
        raise ValueError("検査水準は 1・2・3 のいずれかを指定してください。")

    code: str | None = None
    for (lo, hi), level_map in SAMPLE_SIZE_CODE_TABLE:
        if lo <= lot_size <= hi:
            code = level_map[inspection_level]
            break
    if code is None:
        raise ValueError(f"ロットサイズ {lot_size} はテーブル範囲外です（上限: 500,000）。")

    key = (code, aql)
    if key not in AQL_TABLE:
        raise ValueError(
            f"コード '{code}'、AQL {aql}% の組み合わせはテーブルに定義されていません。"
            " AQL 水準またはロットサイズを変更してください。"
        )

    n, ac, re = AQL_TABLE[key]
    return {"code": code, "n": n, "ac": ac, "re": re}


def oc_curve(n: int, ac: int, p_values: list[float]) -> list[float]:
    """二項分布累積で OC 曲線の Pa 値列を計算する。"""
    return [float(binom.cdf(ac, n, p)) for p in p_values]


def judge_lot(defects: int, ac: int) -> dict:
    """実際の不良数と Ac を比較してロット合否を判定する。"""
    if defects <= ac:
        return {"result": "accept", "verdict": "good"}
    return {"result": "reject", "verdict": "alert"}


def run_plan(lot_size: int, aql: float, inspection_level: int = 2) -> dict:
    """計画設計の全出力をまとめて返す。"""
    plan = get_sampling_plan(lot_size, aql, inspection_level)
    n, ac = plan["n"], plan["ac"]

    oc_p_arr = np.linspace(0.0, 0.20, 200)
    oc_pa_arr = oc_curve(n, ac, list(oc_p_arr))

    alpha = 1.0 - float(binom.cdf(ac, n, aql / 100.0))

    rql_idx = next(
        (i for i, pa in enumerate(oc_pa_arr) if pa <= 0.10),
        len(oc_pa_arr) - 1,
    )
    rql  = float(oc_p_arr[rql_idx])
    beta = oc_pa_arr[rql_idx]

    return {
        "code":  plan["code"],
        "n":     n,
        "ac":    ac,
        "re":    plan["re"],
        "oc_p":  list(oc_p_arr),
        "oc_pa": oc_pa_arr,
        "alpha": alpha,
        "rql":   rql,
        "beta":  beta,
    }

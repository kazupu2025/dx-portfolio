"""Western Electric 異常8ルール判定。X-bar 管理図に全8ルールを適用する。"""
from __future__ import annotations


def detect_violations(
    xbars: list[float],
    cl: float,
    sigma: float,
) -> dict[int, list[int]]:
    """
    X-bar 系列に Western Electric 8ルールを適用し、違反インデックスを返す。

    Parameters
    ----------
    xbars : list[float]
        サブグループ平均値のリスト（時系列順）
    cl : float
        中心線（x̄̄）
    sigma : float
        推定標準偏差（σ̂ = R̄/d₂）

    Returns
    -------
    dict[int, list[int]]
        {ルール番号: [違反したサブグループの index, ...]}
    """
    n = len(xbars)
    result: dict[int, list[int]] = {i: [] for i in range(1, 9)}

    for i in range(n):
        x = xbars[i]

        # Rule 1: 1点が ±3σ 外
        if abs(x - cl) > 3 * sigma:
            result[1].append(i)

        # Rule 2: 連続3点中2点が同側2σ外
        if i >= 2:
            w = xbars[i - 2 : i + 1]
            if (sum(v - cl > 2 * sigma for v in w) >= 2
                    or sum(cl - v > 2 * sigma for v in w) >= 2):
                result[2].append(i)

        # Rule 3: 連続5点中4点が同側1σ外
        if i >= 4:
            w = xbars[i - 4 : i + 1]
            if (sum(v - cl > sigma for v in w) >= 4
                    or sum(cl - v > sigma for v in w) >= 4):
                result[3].append(i)

        # Rule 4: 連続8点が中心線の同側
        if i >= 7:
            w = xbars[i - 7 : i + 1]
            if all(v > cl for v in w) or all(v < cl for v in w):
                result[4].append(i)

        # Rule 5: 連続6点が単調増加 or 単調減少
        if i >= 5:
            w = xbars[i - 5 : i + 1]
            diffs = [w[j + 1] - w[j] for j in range(5)]
            if all(d > 0 for d in diffs) or all(d < 0 for d in diffs):
                result[5].append(i)

        # Rule 6: 連続14点が交互に上下
        if i >= 13:
            w = xbars[i - 13 : i + 1]
            diffs = [w[j + 1] - w[j] for j in range(13)]
            if all(diffs[j] * diffs[j + 1] < 0 for j in range(12)):
                result[6].append(i)

        # Rule 7: 連続15点が ±1σ 内（ハガーリング）
        if i >= 14:
            w = xbars[i - 14 : i + 1]
            if all(abs(v - cl) < sigma for v in w):
                result[7].append(i)

        # Rule 8: 連続8点が全て ±1σ 外（両側混在）
        if i >= 7:
            w = xbars[i - 7 : i + 1]
            if all(abs(v - cl) > sigma for v in w):
                result[8].append(i)

    return result


def rule1_r(rs: list[float], r_ucl: float) -> list[int]:
    """R 管理図 Rule 1: UCL を超過したサブグループの index を返す。"""
    return [i for i, r in enumerate(rs) if r > r_ucl]

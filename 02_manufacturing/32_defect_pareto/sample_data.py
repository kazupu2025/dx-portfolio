"""5不良モード × 6ヶ月 パレート分析デモデータ生成。"""
from __future__ import annotations
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    """5不良モード × 6ヶ月 = 30行のサンプルデータを生成する。

    列: month, defect_mode, count
    期待値: top_pareto_count=2（寸法不良+外観傷で80%超） → verdict="good"
            top_mode: 寸法不良
    """
    months = ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]
    data = {
        "寸法不良": [30, 32, 28, 33, 30, 31],  # 最多
        "外観傷":   [20, 21, 19, 22, 20, 21],   # 2位
        "接着不良": [8,   8,  7,  9,  8,  8],
        "バリ":     [5,   5,  4,  5,  5,  5],
        "その他":   [3,   3,  3,  3,  3,  3],
    }
    # 寸法不良+外観傷 = ~184+123 = 307/430 ≈ 71%（2モードで約71%）
    # → cumulative_pct<=80 が 2モード → top_pareto_count=2 → "good"
    rows = []
    for mode, counts in data.items():
        for i, month in enumerate(months):
            rows.append({"month": month, "defect_mode": mode, "count": counts[i]})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_sample_csv()
    totals = df.groupby("defect_mode")["count"].sum().sort_values(ascending=False)
    total = totals.sum()
    cumsum = totals.cumsum() / total * 100
    print("不良モード別合計（降順）:\n", totals)
    print("\n累積%:\n", cumsum.round(1))
    df.to_csv("sample_defect_pareto.csv", index=False)

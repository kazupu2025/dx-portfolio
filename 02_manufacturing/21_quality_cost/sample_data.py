"""6ヶ月（2024-01〜2024-06）× 4分類 品質コスト デモデータ生成。"""
from __future__ import annotations
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    """6ヶ月 × 4分類 = 24行のサンプルデータを生成する。

    列: month, category, amount
    期待値: failure_ratio ≈ 46% → verdict = "warning"
            dominant_category: 評価コスト
    """
    months = ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]

    data = {
        "予防コスト":    [150000, 155000, 148000, 152000, 160000, 145000],
        "評価コスト":    [200000, 210000, 195000, 205000, 215000, 200000],
        "内部損失コスト": [180000, 175000, 185000, 170000, 190000, 178000],
        "外部損失コスト": [120000, 130000, 115000, 125000, 135000, 118000],
    }

    rows = []
    for cat, amounts in data.items():
        for i, month in enumerate(months):
            rows.append({
                "month":    month,
                "category": cat,
                "amount":   amounts[i],
            })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_sample_csv()
    total = df["amount"].sum()
    n_months = df["month"].nunique()
    avg = total / n_months
    failure = df[df["category"].isin(["内部損失コスト", "外部損失コスト"])]["amount"].sum()
    ratio = failure / total * 100
    print(f"total={total:,}, avg_monthly={avg:,.0f}, failure_ratio={ratio:.1f}%")
    df.to_csv("sample_quality_cost.csv", index=False)

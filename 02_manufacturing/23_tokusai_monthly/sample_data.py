"""5理由 × 6ヶ月 特採件数デモデータ生成。"""
from __future__ import annotations
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    """5理由 × 6ヶ月 = 30行のサンプルデータを生成する。

    列: month, reason, count
    期待値: avg_monthly ≈ 7件 → verdict = "warning"
            top_reason: 寸法軽微逸脱
    """
    months = ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]

    data = {
        "寸法軽微逸脱":   [3, 4, 3, 4, 3, 4],
        "外観不良":       [2, 2, 1, 2, 2, 1],
        "機能上問題なし": [1, 1, 1, 1, 1, 1],
        "材料代替":       [1, 0, 1, 0, 1, 0],
        "その他":         [0, 1, 0, 1, 0, 1],
    }

    rows = []
    for reason, counts in data.items():
        for i, month in enumerate(months):
            rows.append({"month": month, "reason": reason, "count": counts[i]})

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_sample_csv()
    total = df["count"].sum()
    avg = total / df["month"].nunique()
    top = df.groupby("reason")["count"].sum().idxmax()
    print(f"total={total}, avg_monthly={avg:.1f}, top_reason={top}")
    df.to_csv("sample_tokusai.csv", index=False)

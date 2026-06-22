"""4変更種別 × 6ヶ月 4M変更台帳デモデータ生成。"""
from __future__ import annotations
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    """4変更種別 × 6ヶ月 = 24行のサンプルデータを生成する。

    列: month, change_type, count
    期待値: avg_monthly ≈ 8件 → verdict = "warning"
            top_change_type: 設備変更
    """
    months = ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]
    data = {
        "人員変更": [2, 3, 2, 3, 2, 2],
        "設備変更": [4, 5, 4, 5, 4, 5],
        "材料変更": [1, 1, 2, 1, 2, 1],
        "方法変更": [1, 2, 1, 2, 1, 1],
    }
    rows = []
    for ct, counts in data.items():
        for i, month in enumerate(months):
            rows.append({"month": month, "change_type": ct, "count": counts[i]})
    # avg_monthly ≈ 8件 → warning / top=設備変更
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_sample_csv()
    total = df["count"].sum()
    avg = total / df["month"].nunique()
    top = df.groupby("change_type")["count"].sum().idxmax()
    print(f"total={total}, avg_monthly={avg:.1f}, top={top}")
    df.to_csv("sample_4m_change.csv", index=False)

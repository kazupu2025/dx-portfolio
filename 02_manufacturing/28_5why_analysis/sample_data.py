"""5原因カテゴリ × 6ヶ月 なぜなぜ分析デモデータ生成。"""
from __future__ import annotations
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    """5原因カテゴリ × 6ヶ月 = 30行のサンプルデータを生成する。

    列: month, cause_category, count, recurrence
    期待値: recurrence_rate ≈ 20% → verdict = "warning"
            top_cause_category: 設備要因（最多件数）
    """
    months = ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]
    data = {
        # (count_per_month, recurrence_per_month)
        "設備要因": ([5,6,5,6,5,6], [1,1,2,1,1,1]),
        "材料要因": ([3,3,4,3,3,4], [1,0,1,1,0,1]),
        "方法要因": ([2,2,2,2,2,2], [1,1,0,1,1,0]),
        "人的要因": ([4,4,4,4,4,4], [1,1,1,1,1,1]),
        "環境要因": ([1,1,1,1,1,1], [0,0,0,0,0,0]),
    }
    # total_count≈90, total_recurrence≈18 → recurrence_rate≈20% → warning
    rows = []
    for cat, (counts, recs) in data.items():
        for i, month in enumerate(months):
            rows.append({"month": month, "cause_category": cat,
                         "count": counts[i], "recurrence": recs[i]})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_sample_csv()
    total_c = df["count"].sum()
    total_r = df["recurrence"].sum()
    rate = total_r / total_c * 100
    top = df.groupby("cause_category")["count"].sum().idxmax()
    print(f"total_count={total_c}, total_recurrence={total_r}, rate={rate:.1f}%, top={top}")
    df.to_csv("sample_5why_analysis.csv", index=False)

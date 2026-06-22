"""6ヶ月（2024-01〜2024-06）CAPA 実績デモデータ生成。"""
from __future__ import annotations
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    """6ヶ月 = 6行のサンプルデータを生成する。

    列: month, total, completed, on_time_completed
    期待値: completion_rate ≈ 82.7% → verdict = "warning"
            ontime_rate ≈ 72.0%
    """
    data = {
        "month":             ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"],
        "total":             [12,        15,        10,        13,        14,        11],
        "completed":         [10,        13,        8,         10,        12,        9],
        "on_time_completed": [9,         11,        8,         8,         10,        8],
    }
    return pd.DataFrame(data)


if __name__ == "__main__":
    df = generate_sample_csv()
    total = df["total"].sum()
    comp  = df["completed"].sum()
    ontime = df["on_time_completed"].sum()
    print(f"total={total}, completion_rate={comp/total*100:.1f}%, ontime_rate={ontime/total*100:.1f}%")
    df.to_csv("sample_capa_report.csv", index=False)

"""4工程 × 4不良コード × 6ヶ月 工程別不良頻度デモデータ生成。"""
from __future__ import annotations
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    """4工程 × 4不良コード × 6ヶ月 = 96行のサンプルデータを生成する。

    列: month, process, defect_code, count
    期待値: avg_monthly ≈ 20件 → verdict = "warning"
            top_process: 切削工程, top_defect_code: D001
    """
    months = ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]
    processes = ["切削工程", "溶接工程", "組立工程", "検査工程"]
    defect_codes = ["D001", "D002", "D003", "D004"]

    # 工程ごとの不良分布（切削工程が最多）
    base_counts = {
        ("切削工程", "D001"): 5, ("切削工程", "D002"): 2, ("切削工程", "D003"): 1, ("切削工程", "D004"): 1,
        ("溶接工程", "D001"): 2, ("溶接工程", "D002"): 3, ("溶接工程", "D003"): 2, ("溶接工程", "D004"): 1,
        ("組立工程", "D001"): 1, ("組立工程", "D002"): 2, ("組立工程", "D003"): 1, ("組立工程", "D004"): 2,
        ("検査工程", "D001"): 1, ("検査工程", "D002"): 1, ("検査工程", "D003"): 1, ("検査工程", "D004"): 0,
    }

    import random
    random.seed(42)
    rows = []
    for month in months:
        for proc in processes:
            for code in defect_codes:
                base = base_counts[(proc, code)]
                count = max(0, base + random.randint(-1, 1))
                rows.append({"month": month, "process": proc, "defect_code": code, "count": count})
    # avg_monthly ≈ 20件 → warning
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_sample_csv()
    total = df["count"].sum()
    avg = total / df["month"].nunique()
    top_p = df.groupby("process")["count"].sum().idxmax()
    top_d = df.groupby("defect_code")["count"].sum().idxmax()
    print(f"total={total}, avg_monthly={avg:.1f}, top_process={top_p}, top_defect={top_d}")
    df.to_csv("sample_process_defect.csv", index=False)

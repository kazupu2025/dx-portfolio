"""4検査員 × 6ヶ月 検査員別性能デモデータ生成。"""
from __future__ import annotations
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    """4検査員 × 6ヶ月 = 24行のサンプルデータを生成する。

    列: month, inspector, inspected, defects
    期待値: overall_defect_rate ≈ 2.0% → verdict = "warning"
            top_inspector: 田中太郎（最高検出率）
    """
    months = ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]
    # 田中が最高検出率（優秀な検査員）
    data = {
        "田中太郎": {"inspected": [100,105,100,110,100,105], "defects": [4,4,3,4,3,4]},
        "山田花子": {"inspected": [90, 95, 90, 95, 90, 95], "defects": [2,2,2,2,1,2]},
        "鈴木一郎": {"inspected": [120,125,120,125,120,125], "defects": [2,2,2,2,2,2]},
        "佐藤次郎": {"inspected": [80, 85, 80, 85, 80, 85], "defects": [1,1,1,1,1,1]},
    }
    # overall_defect_rate ≈ 2.0% → warning
    rows = []
    for inspector, vals in data.items():
        for i, month in enumerate(months):
            rows.append({"month": month, "inspector": inspector,
                         "inspected": vals["inspected"][i], "defects": vals["defects"][i]})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_sample_csv()
    total_i = df["inspected"].sum()
    total_d = df["defects"].sum()
    rate = total_d / total_i * 100
    top = df.groupby("inspector").apply(lambda g: g["defects"].sum() / g["inspected"].sum() * 100).idxmax()
    print(f"total_inspected={total_i}, total_defects={total_d}, overall_rate={rate:.2f}%, top={top}")
    df.to_csv("sample_inspector_performance.csv", index=False)

"""4仕入先 品質複合スコアリング デモデータ生成。"""
from __future__ import annotations
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    """4仕入先のサンプルデータを生成する。

    列: supplier, defect_rate, cpk, claim_count
    期待値: avg_score ≈ 70点 → verdict = "warning"
            best_supplier: 鈴木部品, worst_supplier: 佐藤工業
    """
    return pd.DataFrame({
        "supplier":    ["鈴木部品",  "田中金属",  "山本鋳造",  "佐藤工業"],
        "defect_rate": [0.5,         2.0,         3.0,         5.0],
        "cpk":         [1.5,         1.3,         1.1,         0.9],
        "claim_count": [1,           3,           5,           10],
    })
    # 鈴木部品: defect_score=95, cpk_score≈89.8, claim_score=95 → total≈92.9
    # 佐藤工業: defect_score=50, cpk_score≈53.9, claim_score=50 → total≈52.4
    # avg ≈ 70点 → warning


if __name__ == "__main__":
    df = generate_sample_csv()
    print(df)
    df.to_csv("sample_supplier_scoring.csv", index=False)

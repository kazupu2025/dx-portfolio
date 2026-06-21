"""5仕入先（SUP-A〜SUP-E）品質指標デモCSV生成。"""
from __future__ import annotations
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    return pd.DataFrame({
        "supplier_id":    ["SUP-A", "SUP-B", "SUP-C", "SUP-D", "SUP-E"],
        "defect_rate":    [1.2,     3.5,     0.8,     5.0,     2.1],
        "delivery_rate":  [95.0,    88.0,    98.0,    82.0,    91.0],
        "price_variance": [3.0,     8.0,     1.5,     12.0,    4.5],
    })
    # 期待スコア（参考）:
    # SUP-A: composite≈89.5 → good
    # SUP-B: composite≈70.9 → warning
    # SUP-C: composite≈93.9 → good
    # SUP-D: composite≈57.6 → alert
    # SUP-E: composite≈82.3 → good
    # avg≈78.8 → warning（全体verdict）


if __name__ == "__main__":
    df = generate_sample_csv()
    df.to_csv("sample_supplier_scoring.csv", index=False)
    print(df.to_string())

"""6ヶ月 出荷検査実績デモデータ生成。"""
from __future__ import annotations
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    """6ヶ月 = 6行のサンプルデータを生成する。

    列: month, inspected, passed, hold_count
    期待値: pass_rate ≈ 97% → verdict = "warning"
            hold_rate ≈ 1.5%
    """
    data = {
        "month":      ["2024-01","2024-02","2024-03","2024-04","2024-05","2024-06"],
        "inspected":  [500,       520,       480,       510,       530,       490],
        "passed":     [485,       506,       466,       497,       515,       477],
        "hold_count": [8,         9,         7,         8,         10,        7],
    }
    # pass_rate = 2946/3030 ≈ 97.2% → warning (95≤rate<99)
    # hold_rate ≈ 1.5%
    return pd.DataFrame(data)


if __name__ == "__main__":
    df = generate_sample_csv()
    total_i = df["inspected"].sum()
    total_p = df["passed"].sum()
    total_h = df["hold_count"].sum()
    print(f"pass_rate={total_p/total_i*100:.1f}%, hold_rate={total_h/total_i*100:.1f}%")
    df.to_csv("sample_shipping_inspection.csv", index=False)

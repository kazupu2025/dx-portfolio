"""6ヶ月 工程パラメータ × 不良率 相関分析デモデータ生成。"""
from __future__ import annotations
import numpy as np
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    """6ヶ月のサンプルデータを生成する。

    列: month, temp_c, pressure_mpa, speed_rpm, defect_rate
    期待値: temp_c が defect_rate と最も強い相関 (|r| ≈ 0.85)
            max_abs_corr ≥ 0.7 → verdict = "good"
    """
    rng = np.random.default_rng(42)
    months = ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]
    # 温度が高いほど不良率が上がる強い正相関
    temp_c        = [220, 225, 218, 230, 222, 228]
    defect_rate   = [t * 0.05 + rng.normal(0, 0.5) for t in temp_c]
    pressure_mpa  = [rng.uniform(2.8, 3.2) for _ in months]  # 相関なし
    speed_rpm     = [rng.uniform(480, 520) for _ in months]   # 相関なし
    return pd.DataFrame({
        "month":        months,
        "temp_c":       [round(t, 1) for t in temp_c],
        "pressure_mpa": [round(p, 3) for p in pressure_mpa],
        "speed_rpm":    [round(s, 1) for s in speed_rpm],
        "defect_rate":  [round(d, 3) for d in defect_rate],
    })


if __name__ == "__main__":
    df = generate_sample_csv()
    print(df)
    corr = df.drop("month", axis=1).corr()["defect_rate"]
    print("\ndefect_rateとの相関:\n", corr)
    df.to_csv("sample_process_correlation.csv", index=False)

"""品質コストROI分析 — 6ヶ月 Wide形式デモデータ生成。"""
from __future__ import annotations
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    """6ヶ月の品質コストデータを生成する。

    列: month, prevention_cost, appraisal_cost, internal_failure, external_failure
    単位: 万円
    期待値:
        total_prevention = 80+82+87+87+91+93 = 520
        first_failure = 40+20 = 60
        last_failure  = 28+10 = 38
        roi = (60-38)/520*100 ≈ 4.2% → verdict="warning"
    """
    return pd.DataFrame({
        "month":            ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"],
        "prevention_cost":  [50, 52, 55, 55, 58, 60],
        "appraisal_cost":   [30, 30, 32, 32, 33, 33],
        "internal_failure": [40, 38, 35, 32, 30, 28],
        "external_failure": [20, 18, 16, 14, 12, 10],
    })


if __name__ == "__main__":
    df = generate_sample_csv()
    total_prevention = (df["prevention_cost"] + df["appraisal_cost"]).sum()
    first_failure = df["internal_failure"].iloc[0] + df["external_failure"].iloc[0]
    last_failure  = df["internal_failure"].iloc[-1] + df["external_failure"].iloc[-1]
    roi = (first_failure - last_failure) / total_prevention * 100
    print(f"total_prevention = {total_prevention}")
    print(f"first_failure = {first_failure}, last_failure = {last_failure}")
    print(f"ROI = {roi:.2f}% → verdict=warning")
    df.to_csv("sample_quality_roi.csv", index=False)
    print(f"\n{len(df)} 行 → sample_quality_roi.csv に保存")

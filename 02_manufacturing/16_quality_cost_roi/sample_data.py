"""12ヶ月（2024-01〜2024-12）品質コストデモCSV生成。"""
from __future__ import annotations
import numpy as np
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = 12
    months = [f"2024-{m:02d}" for m in range(1, n + 1)]
    prevention = np.linspace(500_000, 700_000, n) + rng.normal(0, 10_000, n)
    appraisal  = np.linspace(300_000, 250_000, n) + rng.normal(0, 8_000, n)
    failure    = np.linspace(1_500_000, 600_000, n) + rng.normal(0, 30_000, n)
    return pd.DataFrame({
        "month":            months,
        "prevention_cost":  prevention.round(0).astype(int),
        "appraisal_cost":   appraisal.round(0).astype(int),
        "failure_cost":     failure.round(0).astype(int),
    })


if __name__ == "__main__":
    df = generate_sample_csv()
    df.to_csv("sample_quality_cost.csv", index=False)
    print(df.to_string())

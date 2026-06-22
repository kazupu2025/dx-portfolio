"""AQL/受入サンプリング計画最適化 — 3検査計画デモデータ生成。"""
from __future__ import annotations
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    """3検査計画のサンプルデータを生成する。

    列: lot_size, sample_size, acceptance_number, aql_pct
    期待値:
        各計画で pa_at_aql ≈ 0.97〜0.99 → avg_pa_at_aql > 0.95 → verdict="good"
    """
    return pd.DataFrame({
        "lot_size":          [1000, 500, 2000],
        "sample_size":       [50,   32,  80],
        "acceptance_number": [2,    1,   3],
        "aql_pct":           [1.0,  1.0, 1.0],
    })


if __name__ == "__main__":
    from scipy.stats import binom
    import numpy as np
    df = generate_sample_csv()
    for _, row in df.iterrows():
        n = int(row["sample_size"])
        c = int(row["acceptance_number"])
        aql = row["aql_pct"] / 100
        rql = aql * 10
        pa_aql = binom.cdf(c, n, aql)
        pa_rql = binom.cdf(c, n, rql)
        print(f"lot={row['lot_size']}: pa_at_aql={pa_aql:.4f}, pa_at_rql={pa_rql:.4f}, "
              f"protection={pa_aql-pa_rql:.4f}")
    df.to_csv("sample_aql_sampling.csv", index=False)
    print(f"\n{len(df)} 行 → sample_aql_sampling.csv に保存")

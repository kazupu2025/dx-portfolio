"""工程間品質相関分析 デモ用サンプルデータ生成。"""
from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path


def generate_sample_csv(path: str | None = None) -> pd.DataFrame:
    """
    5工程（A〜E）× 50ロットのデモデータを生成する。

    相関設定:
    - process_A → process_B: r ≈ 0.85（強い正相関）
    - process_B → process_C: r ≈ 0.75（強い正相関）
    - process_D, process_E: A と無相関（独立）

    → max_abs_r ≥ 0.7 → verdict = "good"（強い相関あり）が期待される
    """
    rng = np.random.default_rng(42)
    n = 50

    process_A = rng.normal(10.0, 2.0, n)
    process_B = 0.9 * process_A + rng.normal(0, 0.8, n)
    process_C = 0.8 * process_B + rng.normal(0, 1.2, n)
    process_D = rng.normal(8.0, 1.5, n)
    process_E = rng.normal(5.0, 1.0, n)

    df = pd.DataFrame({
        "lot_id":    [f"L{i+1:03d}" for i in range(n)],
        "process_A": np.round(process_A, 4),
        "process_B": np.round(process_B, 4),
        "process_C": np.round(process_C, 4),
        "process_D": np.round(process_D, 4),
        "process_E": np.round(process_E, 4),
    })
    if path:
        df.to_csv(path, index=False, encoding="utf-8-sig")
    return df


if __name__ == "__main__":
    out = Path(__file__).parent / "sample_process_correlation.csv"
    generate_sample_csv(str(out))
    print(f"Generated: {out}")

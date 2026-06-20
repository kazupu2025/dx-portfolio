"""ゲージR&R デモ用サンプルデータ生成。"""
from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path


def generate_sample_csv(path: str | None = None) -> pd.DataFrame:
    """
    3作業者 × 10部品 × 3繰り返し = 90行のサンプルデータを生成する。

    意図的な違反:
    - 作業者「鈴木」: 全部品に +0.8 のバイアス（高 AV → 再現性悪化）
    - 部品 P05: 測定ノイズが2倍（高 EV → 繰り返し性悪化）
    """
    rng = np.random.default_rng(42)

    true_values = {
        "P01": 10.0, "P02": 11.5, "P03":  8.8, "P04": 12.2, "P05": 10.5,
        "P06":  9.3, "P07": 11.0, "P08":  9.7, "P09": 12.8, "P10": 10.2,
    }
    operator_bias  = {"田中": 0.0, "佐藤": 0.0, "鈴木": 0.8}
    noise_sd_base  = 0.15

    rows: list[dict] = []
    for part, true_val in true_values.items():
        noise_sd = noise_sd_base * 2 if part == "P05" else noise_sd_base
        for op, bias in operator_bias.items():
            for trial in range(1, 4):
                value = true_val + bias + rng.normal(0, noise_sd)
                rows.append({
                    "part":     part,
                    "operator": op,
                    "trial":    trial,
                    "value":    round(float(value), 4),
                })

    df = pd.DataFrame(rows)
    if path:
        df.to_csv(path, index=False, encoding="utf-8-sig")
    return df


if __name__ == "__main__":
    out = Path(__file__).parent / "sample_gauge_rr.csv"
    generate_sample_csv(str(out))
    with open(out, encoding="utf-8-sig") as f:
        row_count = len(f.readlines()) - 1
    print(f"Generated: {out}  ({row_count} rows)")

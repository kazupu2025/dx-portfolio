"""デモ用 SPC サンプルデータ生成。工程ごとに意図的な違反を埋め込む。"""
from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path


def generate_sample_csv(path: str | None = None) -> pd.DataFrame:
    """
    3工程×25サブグループ×n=5 のサンプル CSV を生成する。
    溶接: ロット22 に Rule 1（3σ超過）を埋め込む
    塗装: ロット15-20 に Rule 5（6点連続トレンド）を埋め込む
    組立: ロット10-17 に Rule 4（8点連続同側）を埋め込む
    """
    rng = np.random.default_rng(42)
    rows: list[dict] = []
    config = {
        "溶接": {"mean": 10.00, "std": 0.05},
        "塗装": {"mean":  5.00, "std": 0.03},
        "組立": {"mean": 20.00, "std": 0.10},
    }

    for process, cfg in config.items():
        mu, sigma = cfg["mean"], cfg["std"]
        for lot in range(1, 26):
            shift = 0.0
            if process == "溶接" and lot == 22:
                shift = 3.5 * sigma          # Rule 1: 3σ 超過
            elif process == "塗装" and 15 <= lot <= 20:
                shift = (lot - 14) * sigma   # Rule 5: 漸増トレンド
            elif process == "組立" and 10 <= lot <= 17:
                shift = 1.5 * sigma          # Rule 4: 同側に偏る

            for _ in range(5):
                rows.append({
                    "lot_no":  f"L{lot:03d}",
                    "process": process,
                    "value":   round(float(rng.normal(mu + shift, sigma)), 4),
                })

    df = pd.DataFrame(rows)
    if path:
        df.to_csv(path, index=False, encoding="utf-8-sig")
    return df


if __name__ == "__main__":
    out = Path(__file__).parent / "sample_spc.csv"
    generate_sample_csv(str(out))
    with open(out, encoding="utf-8-sig") as f:
        row_count = len(f.readlines()) - 1
    print(f"Generated: {out}  ({row_count} rows)")

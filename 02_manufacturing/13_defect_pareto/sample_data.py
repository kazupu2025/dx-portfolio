"""不良モード別パレート × 時系列 デモ用サンプルデータ生成。"""
from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path


def generate_sample_csv(path: str | None = None) -> pd.DataFrame:
    """
    5不良モード × 12ヶ月（2024-01〜2024-12）= 60行のサンプルデータを生成する。

    設定:
    - バリ: 全体の約50%（vital few に確実に入る）
    - 寸法不良: 約25%
    - 表面傷: 約15%
    - 欠け: 約7%
    - 異物混入: 約3%
    直近月（2024-12）: 前月比 +25% → verdict = "alert" が期待される
    """
    rng = np.random.default_rng(42)
    modes = ["バリ", "寸法不良", "表面傷", "欠け", "異物混入"]
    base_counts = [50, 25, 15, 7, 3]
    months = [f"2024-{m:02d}" for m in range(1, 13)]

    rows = []
    for i, month in enumerate(months):
        scale = 1.25 if i == 11 else 1.0
        for mode, base in zip(modes, base_counts):
            count = max(1, int(base * scale + rng.integers(-3, 4)))
            rows.append({"year_month": month, "defect_mode": mode, "count": count})

    df = pd.DataFrame(rows)
    if path:
        df.to_csv(path, index=False, encoding="utf-8-sig")
    return df


if __name__ == "__main__":
    out = Path(__file__).parent / "sample_defect_pareto.csv"
    generate_sample_csv(str(out))
    print(f"Generated: {out}")

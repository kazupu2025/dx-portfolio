"""4M変更前後 デモ用サンプルデータ生成。"""
from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path


def generate_sample_csv(path: str | None = None) -> pd.DataFrame:
    """
    before 30行 + after 30行 = 60行のサンプルデータを生成する。

    意図的な設定:
    - before: 平均 10.0、std=0.30（正常工程）
    - after:  平均 10.6、std=0.50（4M変更後に悪化）
    → p < 0.05、効果量大 → verdict = "alert" が期待される
    """
    rng = np.random.default_rng(42)

    before_vals = rng.normal(10.0, 0.30, 30)
    after_vals  = rng.normal(10.6, 0.50, 30)

    rows = (
        [{"group": "before", "measurement": round(float(v), 4)} for v in before_vals]
        + [{"group": "after",  "measurement": round(float(v), 4)} for v in after_vals]
    )

    df = pd.DataFrame(rows)
    if path:
        df.to_csv(path, index=False, encoding="utf-8-sig")
    return df


if __name__ == "__main__":
    out = Path(__file__).parent / "sample_4m_change.csv"
    generate_sample_csv(str(out))
    print(f"Generated: {out}  (60 rows)")

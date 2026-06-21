"""是正処置効果検証 デモ用サンプルデータ生成。"""
from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path


def generate_sample_csv(path: str | None = None) -> pd.DataFrame:
    """
    是正前後の不良率(%)データを生成する。

    before: μ=12.0、σ=2.0、n=30（是正前の高い不良率）
    after:  μ=8.0、σ=1.5、n=30（是正後の改善）
    → p < 0.05、効果量大 → verdict = "good"（是正効果確認）が期待される
    """
    rng = np.random.default_rng(42)
    before_vals = rng.normal(12.0, 2.0, 30)
    after_vals  = rng.normal(8.0,  1.5, 30)

    rows = (
        [{"group": "before", "measurement": round(float(v), 4)} for v in before_vals]
        + [{"group": "after",  "measurement": round(float(v), 4)} for v in after_vals]
    )
    df = pd.DataFrame(rows)
    if path:
        df.to_csv(path, index=False, encoding="utf-8-sig")
    return df


if __name__ == "__main__":
    out = Path(__file__).parent / "sample_corrective_action.csv"
    generate_sample_csv(str(out))
    print(f"Generated: {out}")

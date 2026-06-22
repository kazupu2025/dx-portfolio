"""是正処置（8D）効果検証 — 3処置 × 処置前後10サンプルデモデータ生成。"""
from __future__ import annotations
import pandas as pd
import numpy as np


def generate_sample_csv() -> pd.DataFrame:
    """3処置 × 処置前後10サンプル = 60行のサンプルデータを生成する。

    列: action_id, action_name, group, value
    group: "処置前" / "処置後"
    期待値:
        AC001: 有意差あり + 改善 → effective=True
        AC002: 有意差なし → effective=False
        AC003: 有意差あり + 改善 → effective=True
        effective_ratio = 66.7% → verdict="warning"
    """
    rng = np.random.default_rng(42)

    actions = [
        ("AC001", "表面処理条件変更"),
        ("AC002", "作業手順書改訂"),
        ("AC003", "金型温度調整"),
    ]

    params = {
        "AC001": {
            "before": (12.0, 1.0),   # Normal(12, 1) → 明確に大きい
            "after":  (9.0,  0.8),   # Normal(9, 0.8) → 明確に小さい → 改善
        },
        "AC002": {
            "before": (5.0, 0.5),    # Normal(5, 0.5)
            "after":  (5.1, 0.5),    # Normal(5.1, 0.5) → ほぼ差なし
        },
        "AC003": {
            "before": (8.0, 0.6),    # Normal(8, 0.6)
            "after":  (6.0, 0.5),    # Normal(6, 0.5) → 明確に改善
        },
    }

    rows = []
    for action_id, action_name in actions:
        p = params[action_id]
        before_vals = rng.normal(p["before"][0], p["before"][1], 10)
        after_vals  = rng.normal(p["after"][0],  p["after"][1],  10)
        for v in before_vals:
            rows.append({"action_id": action_id, "action_name": action_name,
                         "group": "処置前", "value": round(float(v), 4)})
        for v in after_vals:
            rows.append({"action_id": action_id, "action_name": action_name,
                         "group": "処置後", "value": round(float(v), 4)})

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_sample_csv()
    print(df.groupby(["action_id", "group"])["value"].agg(["mean", "std"]))
    df.to_csv("sample_8d_effectiveness.csv", index=False)
    print(f"\n{len(df)} 行 → sample_8d_effectiveness.csv に保存")

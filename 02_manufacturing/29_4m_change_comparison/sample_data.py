"""3変更 × 変更前後各10サンプル 4M変更比較デモデータ生成。"""
from __future__ import annotations
import numpy as np
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    """3変更 × (変更前10 + 変更後10) = 60行のサンプルデータを生成。

    列: change_id, change_name, group, value
    期待値: CH001/CH003 が有意差あり → significant_ratio=66.7% → "warning"
            best_change: CH001（改善率最大）
    """
    rng = np.random.default_rng(42)
    rows = []

    # CH001: 工具交換A → 明確な改善（有意差あり）
    for v in rng.normal(10.5, 0.8, 10):
        rows.append({"change_id": "CH001", "change_name": "工具交換A", "group": "変更前", "value": round(float(v), 3)})
    for v in rng.normal(9.2, 0.7, 10):
        rows.append({"change_id": "CH001", "change_name": "工具交換A", "group": "変更後", "value": round(float(v), 3)})

    # CH002: 材料ロット変更 → 差なし（有意差なし）
    for v in rng.normal(5.0, 0.5, 10):
        rows.append({"change_id": "CH002", "change_name": "材料ロット変更", "group": "変更前", "value": round(float(v), 3)})
    for v in rng.normal(5.1, 0.5, 10):
        rows.append({"change_id": "CH002", "change_name": "材料ロット変更", "group": "変更後", "value": round(float(v), 3)})

    # CH003: 作業手順改訂 → 明確な改善（有意差あり）
    for v in rng.normal(8.0, 0.6, 10):
        rows.append({"change_id": "CH003", "change_name": "作業手順改訂", "group": "変更前", "value": round(float(v), 3)})
    for v in rng.normal(6.8, 0.5, 10):
        rows.append({"change_id": "CH003", "change_name": "作業手順改訂", "group": "変更後", "value": round(float(v), 3)})

    # significant_ratio = 2/3 = 66.7% → "warning"
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_sample_csv()
    print(df.groupby(["change_id","group"])["value"].agg(["count","mean"]))
    df.to_csv("sample_4m_change_comparison.csv", index=False)

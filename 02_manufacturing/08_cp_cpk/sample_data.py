"""サンプル測定データ生成スクリプト"""
import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

processes = {
    "溶接": {"mean": 10.02, "std": 0.087},   # Cpk≒1.38 良好
    "塗装": {"mean": 9.88,  "std": 0.12},    # Cpk≒0.97 不可（中心ずれ）
    "組立": {"mean": 10.00, "std": 0.15},    # Cpk≒0.89 不可（ばらつき大）
}
N = 200

rows = []
start = pd.Timestamp("2024-01-01")
for proc, params in processes.items():
    values = np.random.normal(params["mean"], params["std"], N)
    dates = pd.date_range(start, periods=N, freq="h")
    for d, v in zip(dates, values):
        rows.append({"日付": d.strftime("%Y-%m-%d"), "工程名": proc, "測定値": round(v, 4)})

df = pd.DataFrame(rows)
out = Path(__file__).parent / "data" / "sample_measurement.csv"
out.parent.mkdir(exist_ok=True)
df.to_csv(out, index=False, encoding="utf-8-sig")
print(f"生成完了: {out}  ({len(df)}行)")

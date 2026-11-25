# -*- coding: utf-8 -*-
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams['font.family'] = 'MS Gothic'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

CSV_PATH = os.path.join(OUTPUT_DIR, "cleaned_worker_kpi_202401.csv")
df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# Chart 1: Zone total processed qty (bar)
zone_agg = df.groupby("zone")["processed_qty"].sum().reset_index()
zone_agg = zone_agg.sort_values("processed_qty", ascending=False)

fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(zone_agg["zone"], zone_agg["processed_qty"], color="steelblue")
ax.set_title("ゾーン別処理件数")
ax.set_xlabel("ゾーン")
ax.set_ylabel("処理件数合計")
plt.tight_layout()
out1 = os.path.join(CHARTS_DIR, "bar_zone_processed.png")
fig.savefig(out1, dpi=100)
plt.close(fig)
print(f"[OK] Chart 1 saved: output/charts/bar_zone_processed.png")

# Chart 2: Task type average throughput (horizontal bar)
task_agg = df.groupby("task_type")["throughput"].mean().reset_index()
task_agg = task_agg.sort_values("throughput", ascending=True)

fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(task_agg["task_type"], task_agg["throughput"], color="coral")
ax.set_title("作業区分別平均スループット")
ax.set_xlabel("平均スループット (件/時間)")
ax.set_ylabel("作業区分")
plt.tight_layout()
out2 = os.path.join(CHARTS_DIR, "bar_task_throughput.png")
fig.savefig(out2, dpi=100)
plt.close(fig)
print(f"[OK] Chart 2 saved: output/charts/bar_task_throughput.png")

# Chart 3: Top 10 workers by error rate (horizontal bar)
worker_err = df.groupby("worker_id")["error_rate"].mean().reset_index()
top10 = worker_err.sort_values("error_rate", ascending=False).head(10)
top10 = top10.sort_values("error_rate", ascending=True)

fig, ax = plt.subplots(figsize=(8, 6))
ax.barh(top10["worker_id"], top10["error_rate"], color="salmon")
ax.set_title("エラー率上位10作業員")
ax.set_xlabel("平均エラー率")
ax.set_ylabel("作業員ID")
plt.tight_layout()
out3 = os.path.join(CHARTS_DIR, "bar_worker_error_top10.png")
fig.savefig(out3, dpi=100)
plt.close(fig)
print(f"[OK] Chart 3 saved: output/charts/bar_worker_error_top10.png")

print("[OK] Visualization complete.")

# -*- coding: utf-8 -*-
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

matplotlib.rcParams['font.family'] = 'MS Gothic'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

CSV_PATH = os.path.join(OUTPUT_DIR, "cleaned_shift_202401.csv")
df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# --- Chart 1: Store total labor cost (horizontal bar) ---
store_cost = df.groupby("store_name")["daily_wage"].sum().sort_values()

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.barh(store_cost.index, store_cost.values, color="#4C72B0")
ax.set_xlabel("総人件費 (円)")
ax.set_title("店舗別総人件費")
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
plt.tight_layout()
out1 = os.path.join(CHARTS_DIR, "bar_store_labor_cost.png")
plt.savefig(out1, dpi=100)
plt.close()
print(f"[OK] Saved: {out1}")

# --- Chart 2: Role average hourly rate (vertical bar) ---
role_rate = df.groupby("role")["hourly_rate"].mean().sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(7, 5))
ax.bar(role_rate.index, role_rate.values, color="#55A868")
ax.set_ylabel("平均時給 (円)")
ax.set_title("役割別平均時給")
ax.set_ylim(0, role_rate.max() * 1.2)
for i, v in enumerate(role_rate.values):
    ax.text(i, v + 5, f"{v:.0f}", ha="center", va="bottom", fontsize=10)
plt.tight_layout()
out2 = os.path.join(CHARTS_DIR, "bar_role_avg_wage.png")
plt.savefig(out2, dpi=100)
plt.close()
print(f"[OK] Saved: {out2}")

# --- Chart 3: Store average staffing gap (color by positive/negative) ---
store_gap = df.groupby("store_name")["staffing_gap"].mean().sort_values()
colors = ["#C44E52" if v < 0 else "#4C72B0" for v in store_gap.values]

fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(store_gap.index, store_gap.values, color=colors)
ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
ax.set_xlabel("平均シフトギャップ (実員数 - 必要人員)")
ax.set_title("店舗別平均シフトギャップ")
surplus_patch = mpatches.Patch(color="#4C72B0", label="余剰")
shortage_patch = mpatches.Patch(color="#C44E52", label="不足")
ax.legend(handles=[surplus_patch, shortage_patch], loc="lower right")
plt.tight_layout()
out3 = os.path.join(CHARTS_DIR, "bar_store_gap.png")
plt.savefig(out3, dpi=100)
plt.close()
print(f"[OK] Saved: {out3}")

print("[OK] visualize.py completed")

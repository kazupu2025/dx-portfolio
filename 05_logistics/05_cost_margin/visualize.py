# -*- coding: utf-8 -*-
"""3枚のチャートを output/charts/ に生成"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

matplotlib.rcParams['font.family'] = 'MS Gothic'

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = OUTPUT_DIR / "cleaned_deliveries_202401.csv"

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# Chart 1: 配送区分別利益率（横棒グラフ）
type_agg = df.groupby("delivery_type").agg(
    avg_profit_margin=("profit_margin", "mean"),
).reset_index().sort_values("avg_profit_margin", ascending=True)

fig, ax = plt.subplots(figsize=(9, 5))
colors = ["#2196F3"] * len(type_agg)
ax.barh(type_agg["delivery_type"], type_agg["avg_profit_margin"] * 100, color=colors)
ax.set_title("配送区分別利益率")
ax.set_xlabel("平均利益率（%）")
ax.set_ylabel("配送区分")
for i, v in enumerate(type_agg["avg_profit_margin"]):
    ax.text(v * 100 + 0.1, i, f"{v*100:.1f}%", va="center", fontsize=10)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "bar_type_margin.png", dpi=150)
plt.close()
print("[OK] bar_type_margin.png 出力完了")

# Chart 2: エリア別粗利合計（縦棒グラフ）
area_agg = df.groupby("area").agg(
    total_gross_profit=("gross_profit", "sum"),
).reset_index().sort_values("total_gross_profit", ascending=False)

fig, ax = plt.subplots(figsize=(8, 5))
bar_colors = ["#4CAF50", "#2196F3", "#FF9800", "#F44336", "#9C27B0"]
ax.bar(area_agg["area"], area_agg["total_gross_profit"],
       color=bar_colors[:len(area_agg)])
ax.set_title("エリア別粗利合計")
ax.set_xlabel("エリア")
ax.set_ylabel("粗利合計（円）")
for i, v in enumerate(area_agg["total_gross_profit"]):
    ax.text(i, v + 500, f"{v:,.0f}", ha="center", va="bottom", fontsize=9)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "bar_area_profit.png", dpi=150)
plt.close()
print("[OK] bar_area_profit.png 出力完了")

# Chart 3: 車両タイプ別km単価（縦棒グラフ）
vehicle_agg = df.groupby("vehicle_type").agg(
    avg_cost_per_km=("cost_per_km", "mean"),
).reset_index().sort_values("avg_cost_per_km", ascending=False)

fig, ax = plt.subplots(figsize=(7, 5))
bar_colors2 = ["#FF5722", "#FF9800", "#FFC107"]
ax.bar(vehicle_agg["vehicle_type"], vehicle_agg["avg_cost_per_km"],
       color=bar_colors2[:len(vehicle_agg)])
ax.set_title("車両タイプ別km単価")
ax.set_xlabel("車両タイプ")
ax.set_ylabel("平均km単価（円/km）")
for i, v in enumerate(vehicle_agg["avg_cost_per_km"]):
    ax.text(i, v + 0.2, f"{v:.2f}", ha="center", va="bottom", fontsize=10)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "bar_vehicle_cpkm.png", dpi=150)
plt.close()
print("[OK] bar_vehicle_cpkm.png 出力完了")

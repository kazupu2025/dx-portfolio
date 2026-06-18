"""不良率集計: グラフ生成"""
import json
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.family"] = "BIZ UDGothic"
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("output")
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

df = pd.read_csv(OUTPUT_DIR / "cleaned_defect_rate.csv", encoding="utf-8-sig")
df["date"] = pd.to_datetime(df["date"])

# 1. ライン別不良率棒グラフ
line_rates = df.groupby("line").apply(
    lambda x: x["defects"].sum() / x["inspected"].sum(), include_groups=False
).sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(10, 5))
colors = ["#dc2626" if r > 0.04 else "#16a34a" for r in line_rates.values]
bars = ax.bar(line_rates.index, line_rates.values * 100, color=colors)
ax.set_title("ライン別不良率", fontsize=14)
ax.set_ylabel("不良率（%）")
ax.bar_label(bars, fmt="%.2f%%", padding=3)
ax.axhline(y=line_rates.mean() * 100, color="#d97706", linestyle="--", label="平均")
ax.legend()
plt.tight_layout()
plt.savefig(CHARTS_DIR / "bar_line_defect.png", dpi=100)
plt.close()

# 2. 日次不良率推移
daily = df.groupby("date").apply(
    lambda x: x["defects"].sum() / x["inspected"].sum(), include_groups=False
)
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(daily.index, daily.values * 100, color="#1e3a5f", linewidth=1.5)
ax.fill_between(daily.index, daily.values * 100, alpha=0.1, color="#1e3a5f")
ax.set_title("日次不良率推移", fontsize=14)
ax.set_ylabel("不良率（%）")
ax.set_xlabel("日付")
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "line_daily_defect.png", dpi=100)
plt.close()

# 3. 製品別×ライン別ヒートマップ
pivot = df.groupby(["product", "line"]).apply(
    lambda x: round(x["defects"].sum() / x["inspected"].sum() * 100, 2), include_groups=False
).unstack(fill_value=0)
fig, ax = plt.subplots(figsize=(10, 6))
im = ax.imshow(pivot.values, cmap="RdYlGn_r", aspect="auto")
ax.set_xticks(range(len(pivot.columns)))
ax.set_xticklabels(pivot.columns)
ax.set_yticks(range(len(pivot.index)))
ax.set_yticklabels(pivot.index)
plt.colorbar(im, ax=ax, label="不良率（%）")
ax.set_title("製品別×ライン別 不良率ヒートマップ", fontsize=14)
for i in range(len(pivot.index)):
    for j in range(len(pivot.columns)):
        ax.text(j, i, f"{pivot.values[i, j]:.1f}%", ha="center", va="center", fontsize=8)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "heatmap_product_line.png", dpi=100)
plt.close()

result = {"passed": 3, "results": [
    {"id": 1, "name": "ライン別棒グラフ", "status": "PASS"},
    {"id": 2, "name": "日次推移折れ線", "status": "PASS"},
    {"id": 3, "name": "製品×ラインヒートマップ", "status": "PASS"},
]}
(OUTPUT_DIR / "result_charts.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
print("グラフ生成完了")

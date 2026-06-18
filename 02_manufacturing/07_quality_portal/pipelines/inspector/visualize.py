"""検査員別実績: グラフ生成"""
import json
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.family"] = "BIZ UDGothic"
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("output")
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

df = pd.read_csv(OUTPUT_DIR / "cleaned_inspector.csv", encoding="utf-8-sig")
df["date"] = pd.to_datetime(df["date"])

# 1. 検査員別合格率棒グラフ
inspector_rates = df.groupby("inspector").apply(
    lambda x: x["passed"].sum() / x["inspected"].sum(), include_groups=False
).sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(10, 5))
colors = ["#16a34a" if r >= 0.95 else "#d97706" if r >= 0.90 else "#dc2626"
          for r in inspector_rates.values]
bars = ax.bar(inspector_rates.index, inspector_rates.values * 100, color=colors)
ax.set_title("検査員別合格率", fontsize=14)
ax.set_ylabel("合格率（%）")
ax.set_ylim(80, 102)
ax.bar_label(bars, fmt="%.1f%%", padding=3)
ax.axhline(y=inspector_rates.mean() * 100, color="#1e3a5f", linestyle="--", label="平均")
ax.legend()
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "bar_inspector_rate.png", dpi=100)
plt.close()

# 2. シフト別合格率比較（グループ棒グラフ）
if "shift" in df.columns and df["shift"].nunique() > 1:
    pivot_shift = df.groupby(["inspector", "shift"]).apply(
        lambda x: x["passed"].sum() / x["inspected"].sum() * 100, include_groups=False
    ).unstack(fill_value=0)
    fig, ax = plt.subplots(figsize=(12, 5))
    x = np.arange(len(pivot_shift.index))
    width = 0.8 / len(pivot_shift.columns)
    for i, shift in enumerate(pivot_shift.columns):
        offset = (i - len(pivot_shift.columns)/2 + 0.5) * width
        ax.bar(x + offset, pivot_shift[shift], width, label=shift)
    ax.set_xticks(x)
    ax.set_xticklabels(pivot_shift.index, rotation=30, ha="right")
    ax.set_title("検査員別×シフト別 合格率", fontsize=14)
    ax.set_ylabel("合格率（%）")
    ax.set_ylim(80, 105)
    ax.legend(title="シフト")
    plt.tight_layout()
else:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.text(0.5, 0.5, "シフトデータなし", ha="center", va="center", fontsize=14)
    ax.axis("off")
plt.savefig(CHARTS_DIR / "bar_shift_compare.png", dpi=100)
plt.close()

# 3. 日次検査数・合格率推移（2軸グラフ）
daily = df.groupby("date").agg(
    inspected=("inspected", "sum"),
    passed=("passed", "sum"),
)
daily["pass_rate"] = daily["passed"] / daily["inspected"] * 100
fig, ax1 = plt.subplots(figsize=(12, 5))
ax1.bar(daily.index, daily["inspected"], color="#93c5fd", alpha=0.7, label="検査数")
ax1.set_ylabel("検査数", color="#1e3a5f")
ax2 = ax1.twinx()
ax2.plot(daily.index, daily["pass_rate"], color="#16a34a", marker=".", linewidth=1.5, label="合格率")
ax2.set_ylabel("合格率（%）", color="#16a34a")
ax2.set_ylim(80, 105)
ax1.set_title("日次検査数・合格率推移", fontsize=14)
plt.xticks(rotation=30, ha="right")
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "line_daily_inspector.png", dpi=100)
plt.close()

result = {"passed": 3, "results": [
    {"id": 1, "name": "検査員別棒グラフ", "status": "PASS"},
    {"id": 2, "name": "シフト別比較", "status": "PASS"},
    {"id": 3, "name": "日次推移", "status": "PASS"},
]}
(OUTPUT_DIR / "result_charts.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
print("グラフ生成完了")

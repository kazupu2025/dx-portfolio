import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import japanize_matplotlib
from pathlib import Path
import yaml

BASE = Path(__file__).parent.parent
OUTPUT_DIR = Path(__file__).parent

with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)
STAGES = config.get("stages", ["問い合わせ", "内見", "申し込み", "成約"])
CONV_ALERT = config.get("conversion_alert_threshold", 0.10)

df = pd.read_csv(OUTPUT_DIR / "cleaned_inquiry_202401.csv", encoding="utf-8-sig")
for col in ["is_contracted", "contract_amount"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

charts_dir = OUTPUT_DIR / "charts"
charts_dir.mkdir(parents=True, exist_ok=True)
total = len(df)

# 1. ファネル棒グラフ
stage_counts = []
for i, stage in enumerate(STAGES):
    reached = df[df["status"].isin(STAGES[i:])].shape[0]
    stage_counts.append(reached)

colors_funnel = ["#2563eb", "#3b82f6", "#60a5fa", "#22c55e"]
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(STAGES, stage_counts, color=colors_funnel)
for bar, cnt in zip(bars, stage_counts):
    pct = cnt / total * 100 if total > 0 else 0
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f"{cnt}件\n({pct:.1f}%)", ha="center", va="bottom", fontsize=10)
ax.set_title("ファネル分析：問い合わせ → 成約（2024年1月）", fontsize=14)
ax.set_ylabel("件数")
plt.tight_layout()
plt.savefig(charts_dir / "bar_funnel.png", dpi=150)
plt.close()
print("Saved: bar_funnel.png")

# 2. 担当者別成約率棒グラフ
agent_conv = df.groupby("agent").agg(
    total=("inquiry_id", "count"),
    contracts=("is_contracted", "sum"),
).copy()
agent_conv["rate"] = agent_conv["contracts"] / agent_conv["total"] * 100
agent_conv = agent_conv.sort_values("rate", ascending=False)

fig, ax = plt.subplots(figsize=(10, 5))
colors_agent = ["#ef4444" if v < CONV_ALERT * 100 else "#2563eb" for v in agent_conv["rate"]]
bars = ax.bar(agent_conv.index, agent_conv["rate"], color=colors_agent)
ax.axhline(y=CONV_ALERT * 100, color="#f97316", linestyle="--",
           label=f"アラートライン ({CONV_ALERT*100:.0f}%)")
ax.set_title("担当者別 成約率（2024年1月）", fontsize=14)
ax.set_ylabel("成約率（%）")
for bar in bars:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h + 0.2,
            f"{h:.1f}%", ha="center", va="bottom", fontsize=9)
ax.legend()
plt.tight_layout()
plt.savefig(charts_dir / "bar_agent_conversion.png", dpi=150)
plt.close()
print("Saved: bar_agent_conversion.png")

# 3. エリア別問い合わせ数・成約率複合グラフ
area_data = df.groupby("area").agg(
    total=("inquiry_id", "count"),
    contracts=("is_contracted", "sum"),
).copy()
area_data["rate"] = area_data["contracts"] / area_data["total"] * 100
area_data = area_data.sort_values("total", ascending=False)

fig, ax1 = plt.subplots(figsize=(10, 5))
ax2 = ax1.twinx()

bars2 = ax1.bar(area_data.index, area_data["total"], color="#2563eb", alpha=0.7, label="問い合わせ数")
line2 = ax2.plot(area_data.index, area_data["rate"], color="#ef4444",
                 marker="o", linewidth=2, markersize=8, label="成約率(%)")
ax2.axhline(y=CONV_ALERT * 100, color="#f97316", linestyle="--", alpha=0.8,
            label=f"アラートライン({CONV_ALERT*100:.0f}%)")

ax1.set_title("エリア別 問い合わせ数・成約率（2024年1月）", fontsize=14)
ax1.set_ylabel("問い合わせ数（件）", color="#2563eb")
ax2.set_ylabel("成約率（%）", color="#ef4444")

handles = ax1.get_legend_handles_labels()[0] + ax2.get_legend_handles_labels()[0]
labels  = ax1.get_legend_handles_labels()[1] + ax2.get_legend_handles_labels()[1]
ax1.legend(handles, labels, loc="upper right")
plt.tight_layout()
plt.savefig(charts_dir / "bar_area_inquiry.png", dpi=150)
plt.close()
print("Saved: bar_area_inquiry.png")

print("グラフ生成完了")

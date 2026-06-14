import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import japanize_matplotlib
from pathlib import Path
import yaml

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = Path(__file__).parent

with open(BASE_DIR / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)
PEAK_THRESHOLD = config.get("peak_hour_threshold", 1.3)
WAIT_ALERT = config.get("wait_alert_minutes", 60)

df = pd.read_csv(OUTPUT_DIR / "cleaned_visit_202401.csv", encoding="utf-8-sig")
for col in ["wait_minutes", "hour_slot"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
if "is_long_wait" in df.columns:
    df["is_long_wait"] = df["is_long_wait"].astype(bool)

charts_dir = OUTPUT_DIR / "charts"
charts_dir.mkdir(parents=True, exist_ok=True)

# 1. 時間帯別来院数棒グラフ
hour_counts = df.groupby("hour_slot").size().reindex(range(9, 18), fill_value=0)
avg = hour_counts.mean()
colors = ["#ef4444" if v > avg * PEAK_THRESHOLD else "#2563eb" for v in hour_counts.values]

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar([f"{h}時" for h in hour_counts.index], hour_counts.values, color=colors)
ax.axhline(y=avg * PEAK_THRESHOLD, color="#f97316", linestyle="--",
           label=f"ピーク閾値（平均×{PEAK_THRESHOLD}）")
ax.set_title("時間帯別 来院数（2024年1月合計）", fontsize=14)
ax.set_ylabel("来院数（件）")
for bar in bars:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h + 1,
            f"{int(h)}", ha="center", va="bottom", fontsize=9)
ax.legend()
plt.tight_layout()
plt.savefig(charts_dir / "bar_hourly_visits.png", dpi=150)
plt.close()
print("Saved: bar_hourly_visits.png")

# 2. 診療科別来院数 & 平均待ち時間（複合グラフ）
dept_visits = df.groupby("department").size().sort_values(ascending=False)
dept_wait   = df.groupby("department")["wait_minutes"].mean().reindex(dept_visits.index)

fig, ax1 = plt.subplots(figsize=(10, 5))
ax2 = ax1.twinx()

bars2 = ax1.bar(dept_visits.index, dept_visits.values, color="#2563eb", alpha=0.7, label="来院数")
line2 = ax2.plot(dept_visits.index, dept_wait.values, color="#ef4444",
                 marker="o", linewidth=2, markersize=8, label="平均待ち(分)")
ax2.axhline(y=WAIT_ALERT, color="#f97316", linestyle="--", alpha=0.7,
            label=f"アラートライン({WAIT_ALERT}分)")

ax1.set_title("診療科別 来院数・平均待ち時間（2024年1月）", fontsize=14)
ax1.set_ylabel("来院数（件）", color="#2563eb")
ax2.set_ylabel("平均待ち時間（分）", color="#ef4444")

lines_labels = [ax1.get_legend_handles_labels(), ax2.get_legend_handles_labels()]
handles = lines_labels[0][0] + lines_labels[1][0]
labels  = lines_labels[0][1] + lines_labels[1][1]
ax1.legend(handles, labels, loc="upper right")
plt.tight_layout()
plt.savefig(charts_dir / "bar_dept_visits.png", dpi=150)
plt.close()
print("Saved: bar_dept_visits.png")

# 3. 曜日×時間帯 来院数ヒートマップ
if "weekday" in df.columns and "hour_slot" in df.columns:
    WEEKDAY_ORDER = ["月", "火", "水", "木", "金", "土", "日"]
    pivot = df.groupby(["weekday", "hour_slot"]).size().unstack(fill_value=0)
    pivot = pivot.reindex([w for w in WEEKDAY_ORDER if w in pivot.index])
    pivot = pivot.reindex(columns=range(9, 18), fill_value=0)
    pivot.columns = [f"{h}時" for h in pivot.columns]

    try:
        import seaborn as sns
        fig, ax = plt.subplots(figsize=(12, 5))
        sns.heatmap(
            pivot, annot=True, fmt="d", cmap="Blues",
            linewidths=0.5,
            cbar_kws={"label": "来院数（件）"},
            ax=ax,
        )
    except ImportError:
        fig, ax = plt.subplots(figsize=(12, 5))
        im = ax.imshow(pivot.values, cmap="Blues", aspect="auto")
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns)
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index)
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                ax.text(j, i, str(pivot.values[i, j]),
                        ha="center", va="center", fontsize=9)
        plt.colorbar(im, ax=ax, label="来院数（件）")

    ax.set_title("曜日×時間帯 来院数ヒートマップ（2024年1月）", fontsize=14)
    ax.set_xlabel("時間帯")
    ax.set_ylabel("曜日")
    plt.tight_layout()
    plt.savefig(charts_dir / "heatmap_weekday_hour.png", dpi=150)
    plt.close()
    print("Saved: heatmap_weekday_hour.png")
else:
    print("WARN: weekday/hour_slot列なし、ヒートマップをスキップ")

print("グラフ生成完了")

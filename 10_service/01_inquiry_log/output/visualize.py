"""
B-15 可視化スクリプト (3チャート)
1. bar_category_inquiry.png  — カテゴリ別件数 + 平均対応時間
2. bar_operator_performance.png — 担当者別解決率 + 平均対応時間
3. bar_hourly_inquiry.png    — 時間帯別受付件数
"""
from pathlib import Path
import pandas as pd
import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# 日本語フォント設定
import matplotlib.font_manager as fm
jp_fonts = ["MS Gothic", "Meiryo", "IPAexGothic", "Noto Sans CJK JP", "DejaVu Sans"]
available = {f.name for f in fm.fontManager.ttflist}
for font in jp_fonts:
    if font in available:
        plt.rcParams["font.family"] = font
        break

BASE = Path(__file__).resolve().parent.parent
OUT  = Path(__file__).resolve().parent
CHARTS = OUT / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

CFG_PATH = BASE / "config.yml"
CSV_PATH = OUT / "cleaned_inquiry_202401.csv"

with open(CFG_PATH, encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
df["received_at"] = pd.to_datetime(df["received_at"], format="%Y-%m-%d %H:%M", errors="coerce")
df["response_minutes"] = pd.to_numeric(df["response_minutes"], errors="coerce")
df["is_resolved"] = df["is_resolved"].astype(int)

# --- Chart 1: カテゴリ別問い合わせ件数 + 平均対応時間 ---
cat_grp = df.groupby("category").agg(
    件数=("inquiry_id", "count"),
    平均対応時間=("response_minutes", "mean"),
).reset_index().sort_values("件数", ascending=False)

fig, ax1 = plt.subplots(figsize=(10, 6))
bars = ax1.bar(cat_grp["category"], cat_grp["件数"], color="#4C72B0", alpha=0.8, label="問い合わせ件数")
ax1.set_xlabel("カテゴリ", fontsize=12)
ax1.set_ylabel("件数", fontsize=12, color="#4C72B0")
ax1.tick_params(axis="y", labelcolor="#4C72B0")
ax1.tick_params(axis="x", rotation=20)

ax2 = ax1.twinx()
line = ax2.plot(cat_grp["category"], cat_grp["平均対応時間"], color="#DD8452",
                marker="o", linewidth=2, markersize=6, label="平均対応時間(分)")
ax2.set_ylabel("平均対応時間(分)", fontsize=12, color="#DD8452")
ax2.tick_params(axis="y", labelcolor="#DD8452")

# 凡例まとめ
handles1 = [mpatches.Patch(color="#4C72B0", alpha=0.8, label="問い合わせ件数")]
handles2 = line
all_handles = handles1 + handles2
ax1.legend(handles=all_handles, loc="upper right", fontsize=10)

plt.title("カテゴリ別問い合わせ件数・平均対応時間", fontsize=14, pad=15)
plt.tight_layout()
p1 = CHARTS / "bar_category_inquiry.png"
plt.savefig(p1, dpi=150, bbox_inches="tight")
plt.close()
print(f"Chart 1: {p1} ({p1.stat().st_size:,} bytes)")

# --- Chart 2: 担当者別解決率 + 平均対応時間 ---
resolution_alert = cfg["resolution_rate_alert"]

op_grp = df.groupby(["operator_id", "operator_name"]).agg(
    解決率=("is_resolved", "mean"),
    平均対応時間=("response_minutes", "mean"),
).reset_index().sort_values("operator_id")

labels = [f"{r['operator_id']}\n{r['operator_name']}" for _, r in op_grp.iterrows()]
colors = ["#DD4444" if r["解決率"] < resolution_alert else "#4C72B0" for _, r in op_grp.iterrows()]

fig, ax1 = plt.subplots(figsize=(12, 6))
bars = ax1.bar(labels, op_grp["解決率"] * 100, color=colors, alpha=0.8)
ax1.axhline(y=resolution_alert * 100, color="red", linestyle="--", linewidth=1.5, label=f"アラート基準 {resolution_alert*100:.0f}%")
ax1.set_xlabel("担当者", fontsize=12)
ax1.set_ylabel("解決率(%)", fontsize=12, color="#333333")
ax1.set_ylim(0, 105)

ax2 = ax1.twinx()
line = ax2.plot(labels, op_grp["平均対応時間"], color="#DD8452",
                marker="o", linewidth=2, markersize=6, label="平均対応時間(分)")
ax2.set_ylabel("平均対応時間(分)", fontsize=12, color="#DD8452")
ax2.tick_params(axis="y", labelcolor="#DD8452")

# 凡例まとめ
h1 = mpatches.Patch(color="#4C72B0", alpha=0.8, label="解決率(%)")
h2 = mpatches.Patch(color="#DD4444", alpha=0.8, label=f"解決率<{resolution_alert*100:.0f}% (要改善)")
h3 = plt.Line2D([0],[0], color="red", linestyle="--", linewidth=1.5, label=f"アラート基準")
h4 = line[0]
ax1.legend(handles=[h1, h2, h3, h4], loc="lower right", fontsize=9)

plt.title("担当者別解決率・平均対応時間", fontsize=14, pad=15)
plt.tight_layout()
p2 = CHARTS / "bar_operator_performance.png"
plt.savefig(p2, dpi=150, bbox_inches="tight")
plt.close()
print(f"Chart 2: {p2} ({p2.stat().st_size:,} bytes)")

# --- Chart 3: 時間帯別受付件数 ---
df["hour"] = df["received_at"].dt.hour
hour_grp = df.groupby("hour")["inquiry_id"].count().reindex(range(9, 18), fill_value=0)
peak_hour = int(hour_grp.idxmax())

colors3 = ["#DD4444" if h == peak_hour else "#4C72B0" for h in hour_grp.index]

fig, ax = plt.subplots(figsize=(10, 6))
ax.bar([f"{h}時" for h in hour_grp.index], hour_grp.values, color=colors3, alpha=0.85)
ax.set_xlabel("時間帯", fontsize=12)
ax.set_ylabel("問い合わせ件数", fontsize=12)
ax.set_title("時間帯別受付件数（ピーク時間帯分析）", fontsize=14, pad=15)

# 凡例
h1 = mpatches.Patch(color="#4C72B0", alpha=0.85, label="通常時間帯")
h2 = mpatches.Patch(color="#DD4444", alpha=0.85, label=f"ピーク ({peak_hour}時)")
ax.legend(handles=[h1, h2], fontsize=10)

plt.tight_layout()
p3 = CHARTS / "bar_hourly_inquiry.png"
plt.savefig(p3, dpi=150, bbox_inches="tight")
plt.close()
print(f"Chart 3: {p3} ({p3.stat().st_size:,} bytes)")

print("可視化完了")

# -*- coding: utf-8 -*-
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd

matplotlib.rcParams['font.family'] = 'MS Gothic'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

ROOM_CSV_PATH = os.path.join(OUTPUT_DIR, "room_summary_202401.csv")
CLEANED_PATH = os.path.join(OUTPUT_DIR, "cleaned_reservations_202401.csv")

room_df = pd.read_csv(ROOM_CSV_PATH, encoding="utf-8-sig")
df = pd.read_csv(CLEANED_PATH, encoding="utf-8-sig")
df["checkin_date"] = pd.to_datetime(df["checkin_date"].astype(str).str.replace("/", "-", regex=False), format="%Y-%m-%d")

# 1. Bar chart: room type total revenue
fig, ax = plt.subplots(figsize=(8, 5))
colors = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0"]
bars = ax.bar(room_df["room_type"], room_df["total_revenue"] / 10000, color=colors, edgecolor="white", linewidth=0.5)
ax.set_title("客室タイプ別総売上", fontsize=14, fontweight="bold")
ax.set_xlabel("客室タイプ")
ax.set_ylabel("総売上（万円）")
ax.set_ylim(0, room_df["total_revenue"].max() / 10000 * 1.2)
for bar, val in zip(bars, room_df["total_revenue"]):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + room_df["total_revenue"].max() / 10000 * 0.01,
            "{:,.0f}万".format(val / 10000), ha="center", va="bottom", fontsize=9)
ax.grid(axis="y", alpha=0.3)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "bar_roomtype_revenue.png"), dpi=150, bbox_inches="tight")
plt.close()
print("[OK] bar_roomtype_revenue.png saved")

# 2. Horizontal bar chart: cancel rate by room type (red palette)
fig, ax = plt.subplots(figsize=(8, 5))
cancel_df = room_df.sort_values("cancel_rate")
red_colors = ["#FFCDD2", "#EF9A9A", "#E57373", "#C62828"]
bars = ax.barh(cancel_df["room_type"], cancel_df["cancel_rate"] * 100,
               color=red_colors, edgecolor="white", linewidth=0.5)
ax.set_title("客室タイプ別キャンセル率", fontsize=14, fontweight="bold")
ax.set_xlabel("キャンセル率（%）")
ax.set_ylabel("客室タイプ")
for bar, val in zip(bars, cancel_df["cancel_rate"]):
    ax.text(val * 100 + 0.3, bar.get_y() + bar.get_height() / 2,
            "{:.1f}%".format(val * 100), va="center", fontsize=9)
ax.grid(axis="x", alpha=0.3)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "bar_roomtype_cancel_rate.png"), dpi=150, bbox_inches="tight")
plt.close()
print("[OK] bar_roomtype_cancel_rate.png saved")

# 3. Line chart: daily occupancy rate
daily = df.groupby("checkin_date").agg(
    total=("reserv_no", "count"),
    stayed=("status", lambda x: (x == "宿泊済み").sum()),
).reset_index()
daily["occ_rate"] = daily["stayed"] / daily["total"]
daily = daily.sort_values("checkin_date")

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(daily["checkin_date"], daily["occ_rate"] * 100, color="#1565C0",
        marker="o", markersize=5, linewidth=2, label="稼働率")
ax.fill_between(daily["checkin_date"], daily["occ_rate"] * 100, alpha=0.1, color="#1565C0")
ax.axhline(y=daily["occ_rate"].mean() * 100, color="#E53935", linestyle="--", alpha=0.7, label="平均稼働率")
ax.set_title("日別稼働率推移（2024年1月）", fontsize=14, fontweight="bold")
ax.set_xlabel("チェックイン日")
ax.set_ylabel("稼働率（%）")
ax.set_ylim(0, 105)
ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%m/%d"))
plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")
ax.grid(alpha=0.3)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "line_daily_occupancy.png"), dpi=150, bbox_inches="tight")
plt.close()
print("[OK] line_daily_occupancy.png saved")
print("[OK] All charts saved.")

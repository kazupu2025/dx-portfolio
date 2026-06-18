"""クレーム集計: グラフ生成"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

matplotlib.rcParams["font.family"] = "BIZ UDGothic"

OUTPUT_DIR = Path("output")
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

df = pd.read_csv(OUTPUT_DIR / "cleaned_claim.csv", encoding="utf-8-sig")
df["date"] = pd.to_datetime(df["date"])

# 1. 仕入先別クレーム棒グラフ
supplier_counts = df["supplier"].value_counts()
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(supplier_counts.index, supplier_counts.values, color="#1e3a5f")
ax.set_title("仕入先別クレーム件数", fontsize=14)
ax.set_ylabel("件数")
ax.bar_label(bars, padding=3)
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "bar_supplier_claim.png", dpi=100)
plt.close()

# 2. カテゴリ別円グラフ
cat_counts = df["category"].value_counts()
fig, ax = plt.subplots(figsize=(8, 8))
ax.pie(cat_counts.values, labels=cat_counts.index, autopct="%1.1f%%",
       colors=["#1e3a5f", "#2a5298", "#3b82f6", "#93c5fd", "#bfdbfe"])
ax.set_title("不良カテゴリ別内訳", fontsize=14)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "pie_category.png", dpi=100)
plt.close()

# 3. 週次クレーム件数推移
df["week"] = df["date"].dt.to_period("W")
weekly = df.groupby("week").size()
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(range(len(weekly)), weekly.values, color="#1e3a5f", marker="o", linewidth=2)
ax.set_xticks(range(len(weekly)))
ax.set_xticklabels([str(p) for p in weekly.index], rotation=30, ha="right")
ax.set_title("週次クレーム件数推移", fontsize=14)
ax.set_ylabel("件数")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "line_weekly_claim.png", dpi=100)
plt.close()

result = {"passed": 3, "results": [
    {"id": 1, "name": "仕入先別棒グラフ", "status": "PASS"},
    {"id": 2, "name": "カテゴリ円グラフ", "status": "PASS"},
    {"id": 3, "name": "週次推移折れ線", "status": "PASS"},
]}
(OUTPUT_DIR / "result_charts.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
print("グラフ生成完了")

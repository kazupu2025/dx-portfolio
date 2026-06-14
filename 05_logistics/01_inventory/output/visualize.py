import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import japanize_matplotlib
from pathlib import Path

df = pd.read_csv("output/cleaned_inventory_202401.csv", encoding="utf-8-sig")
for col in ["stock_qty", "min_stock_qty", "unit_cost", "received_qty", "shipped_qty"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

df["stock_value"] = df["stock_qty"] * df["unit_cost"]
df["stockout_flag"] = df["stock_qty"] < df["min_stock_qty"]
df["turnover_rate"] = df.apply(
    lambda r: r["shipped_qty"] / r["stock_qty"] if r["stock_qty"] > 0 else 0.0, axis=1
)

charts_dir = Path("output/charts")
charts_dir.mkdir(parents=True, exist_ok=True)

# 1. 倉庫別在庫金額棒グラフ
wh_stock = df.groupby("warehouse")["stock_value"].sum().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(wh_stock.index, wh_stock.values, color="#2563eb")
ax.set_title("倉庫別在庫金額（2024年1月）", fontsize=14)
ax.set_ylabel("在庫金額（円）")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
for bar in bars:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h + h*0.01,
            f"{h:,.0f}", ha="center", va="bottom", fontsize=9)
plt.tight_layout()
plt.savefig(charts_dir / "bar_warehouse_stock.png", dpi=150)
plt.close()
print("Saved: bar_warehouse_stock.png")

# 2. 倉庫別欠品品目数棒グラフ（赤棒）
stockout_by_wh = df.groupby("warehouse")["stockout_flag"].sum().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(stockout_by_wh.index, stockout_by_wh.values, color="#ef4444")
ax.set_title("倉庫別欠品品目数（2024年1月）", fontsize=14)
ax.set_ylabel("欠品品目数（件）")
for bar, v in zip(bars, stockout_by_wh.values):
    ax.text(bar.get_x() + bar.get_width()/2, v + 0.1,
            str(int(v)), ha="center", va="bottom", fontsize=10)
plt.tight_layout()
plt.savefig(charts_dir / "bar_stockout_items.png", dpi=150)
plt.close()
print("Saved: bar_stockout_items.png")

# 3. 品目別在庫回転率散布図（欠品品目は赤点）
item_stats = df.groupby("item_name").agg(
    turnover=("turnover_rate", "mean"),
    stockout=("stockout_flag", "any"),
    stock_value=("stock_value", "sum"),
).reset_index()
colors = ["#ef4444" if s else "#2563eb" for s in item_stats["stockout"]]
fig, ax = plt.subplots(figsize=(12, 6))
ax.scatter(range(len(item_stats)), item_stats["turnover"], c=colors, alpha=0.7, s=60)
ax.set_title("品目別在庫回転率（赤=欠品品目）（2024年1月）", fontsize=14)
ax.set_ylabel("在庫回転率（shipped / stock）")
ax.set_xlabel("品目インデックス")
from matplotlib.patches import Patch
ax.legend(handles=[
    Patch(color="#ef4444", label="欠品品目"),
    Patch(color="#2563eb", label="正常品目"),
])
plt.tight_layout()
plt.savefig(charts_dir / "scatter_turnover.png", dpi=150)
plt.close()
print("Saved: scatter_turnover.png")

print("グラフ生成完了")

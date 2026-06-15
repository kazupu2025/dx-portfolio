import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import japanize_matplotlib
from pathlib import Path
import yaml

with open("config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

OVERSTOCK_TH = config.get("overstock_days_threshold", 30)

forecast_df = pd.read_csv("output/forecast_202401.csv", encoding="utf-8-sig")
for col in ["avg_daily_sales", "forecast_31days", "recommended_order",
            "days_of_stock", "current_stock", "safety_stock"]:
    if col in forecast_df.columns:
        forecast_df[col] = pd.to_numeric(forecast_df[col], errors="coerce").fillna(0)
forecast_df["stockout_risk"] = forecast_df["stockout_risk"].astype(bool)
forecast_df["overstock"]     = forecast_df["overstock"].astype(bool)

charts_dir = Path("output/charts")
charts_dir.mkdir(parents=True, exist_ok=True)

# 1. カテゴリ別 月次需要予測 + 推奨発注量（twinx）
cat_sum = forecast_df.groupby("category").agg(
    月次予測需要=("forecast_31days",   "sum"),
    推奨発注量合計=("recommended_order", "sum"),
).sort_values("月次予測需要", ascending=False)

fig, ax1 = plt.subplots(figsize=(10, 5))
ax2 = ax1.twinx()
bars = ax1.bar(cat_sum.index, cat_sum["月次予測需要"], color="#2563eb", alpha=0.8, label="月次需要予測")
line = ax2.plot(cat_sum.index, cat_sum["推奨発注量合計"], color="#ef4444",
                marker="o", linewidth=2, label="推奨発注量合計")
ax1.set_title("カテゴリ別 月次需要予測・推奨発注量（2024年1月）", fontsize=13)
ax1.set_ylabel("月次需要予測（個）")
ax2.set_ylabel("推奨発注量合計（個）", color="#ef4444")
ax2.tick_params(axis="y", labelcolor="#ef4444")
lns = bars.patches + line
labels = ["月次需要予測", "推奨発注量合計"]
ax1.legend(lns[:2], labels, loc="upper right")
for bar in bars.patches:
    h = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2, h * 1.01,
             f"{h:,.0f}", ha="center", va="bottom", fontsize=8)
plt.tight_layout()
plt.savefig(charts_dir / "bar_category_forecast.png", dpi=150)
plt.close()
print("Saved: bar_category_forecast.png")

# 2. 欠品リスク商品の現在庫 vs リードタイム需要（横棒グラフ）
risk_df = forecast_df[forecast_df["stockout_risk"]].sort_values("days_of_stock").head(15)
if len(risk_df) == 0:
    # 欠品リスクがない場合は在庫日数が最も少ない商品TOP15
    risk_df = forecast_df.sort_values("days_of_stock").head(15)
    title_suffix = "（在庫日数 少ない順 TOP15）"
else:
    title_suffix = "（欠品リスク商品）"

lead_demand = risk_df["avg_daily_sales"] * config.get("lead_time_days", 3)
colors = ["#ef4444" if r else "#f97316" for r in risk_df["stockout_risk"]]
fig, ax = plt.subplots(figsize=(12, max(5, len(risk_df) * 0.5)))
y = range(len(risk_df))
ax.barh(list(y), risk_df["current_stock"].values, color=colors, label="現在庫")
ax.plot(lead_demand.values, list(y), "k^", markersize=8, label=f"LT需要({config.get('lead_time_days',3)}日分)")
ax.set_yticks(list(y))
ax.set_yticklabels(risk_df["product_name"].tolist(), fontsize=9)
ax.set_title(f"欠品リスク商品 現在庫 vs リードタイム需要{title_suffix}", fontsize=12)
ax.set_xlabel("数量（個）")
ax.legend()
plt.tight_layout()
plt.savefig(charts_dir / "bar_stockout_risk.png", dpi=150)
plt.close()
print("Saved: bar_stockout_risk.png")

# 3. 在庫日数 vs 月次予測需要 散布図
colors_scatter = []
for _, row in forecast_df.iterrows():
    if row["stockout_risk"]:
        colors_scatter.append("#ef4444")
    elif row["overstock"]:
        colors_scatter.append("#f97316")
    else:
        colors_scatter.append("#2563eb")

fig, ax = plt.subplots(figsize=(10, 7))
scatter = ax.scatter(
    forecast_df["forecast_31days"],
    forecast_df["days_of_stock"],
    c=colors_scatter, alpha=0.7, s=60
)
ax.axhline(y=OVERSTOCK_TH, color="#f97316", linestyle="--",
           label=f"過剰在庫ライン ({OVERSTOCK_TH}日)", alpha=0.7)
ax.axhline(y=config.get("lead_time_days", 3), color="#ef4444", linestyle="--",
           label=f"欠品リスクライン ({config.get('lead_time_days',3)}日)", alpha=0.7)
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor="#ef4444", label="欠品リスク"),
    Patch(facecolor="#f97316", label="過剰在庫"),
    Patch(facecolor="#2563eb", label="正常"),
]
ax.legend(handles=legend_elements + [
    plt.Line2D([0], [0], color="#f97316", linestyle="--", label=f"過剰在庫ライン({OVERSTOCK_TH}日)"),
    plt.Line2D([0], [0], color="#ef4444", linestyle="--", label=f"欠品リスクライン({config.get('lead_time_days',3)}日)"),
])
ax.set_title("商品別 在庫日数 vs 月次需要予測（2024年1月）", fontsize=13)
ax.set_xlabel("月次需要予測（個）")
ax.set_ylabel("在庫日数（日）")
plt.tight_layout()
plt.savefig(charts_dir / "scatter_stock_forecast.png", dpi=150)
plt.close()
print("Saved: scatter_stock_forecast.png")

print("グラフ生成完了")

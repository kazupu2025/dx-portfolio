"""
発注最適化・需要予測パイプライン
需要予測・発注最適化分析スクリプト
移動平均 + 曜日係数 + トレンド補正モデルで2024年1月の需要を予測し
推奨発注量・欠品リスク・過剰在庫を商品別に算出する
"""
import pandas as pd
import numpy as np
from datetime import date, timedelta
from pathlib import Path

try:
    import yaml
    with open("config.yml", encoding="utf-8") as f:
        config = yaml.safe_load(f)
except Exception:
    config = {}

WINDOW       = config.get("moving_avg_window", 7)
Z_SAFETY     = config.get("safety_stock_z", 1.65)
LEAD_TIME    = config.get("lead_time_days", 3)
FCAST_DAYS   = config.get("forecast_days", 31)
OVERSTOCK_TH = config.get("overstock_days_threshold", 30)

OUTPUT_DIR = Path("output")

df = pd.read_csv(OUTPUT_DIR / "cleaned_order_2023Q4.csv", encoding="utf-8-sig")
df["date"] = pd.to_datetime(df["date"])
for col in ["sales_qty", "stock_qty", "reorder_point", "order_qty", "lead_time_days"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# 曜日係数（月=0.9, 火=0.85, 水=0.95, 木=1.0, 金=1.2, 土=1.5, 日=1.4）
weekday_factors = [0.9, 0.85, 0.95, 1.0, 1.2, 1.5, 1.4]

forecast_rows = []
stockout_ids = []
overstock_ids = []

for (prod_id, prod_name, cat), grp in df.groupby(
        ["product_id", "product_name", "category"]):
    grp = grp.sort_values("date").copy()

    # 移動平均ベース需要 (直近7日)
    recent = grp.tail(WINDOW)["sales_qty"]
    base_demand = recent.mean() if len(recent) >= 3 else grp["sales_qty"].mean()
    if base_demand != base_demand or base_demand <= 0:
        base_demand = 1.0
    demand_std = grp["sales_qty"].std()
    if demand_std != demand_std or demand_std <= 0:
        demand_std = 1.0

    # トレンド係数 (直近30日 vs 全体平均)
    last_30 = grp.tail(30)["sales_qty"].mean()
    total_avg = grp["sales_qty"].mean()
    trend_factor = last_30 / total_avg if total_avg > 0 else 1.0
    trend_factor = float(np.clip(trend_factor, 0.5, 2.0))

    # 現在の在庫（最終レコード）
    last_row = grp.iloc[-1]
    current_stock = float(last_row["stock_qty"])
    lead_time = int(last_row.get("lead_time_days", LEAD_TIME) or LEAD_TIME)

    # 安全在庫
    safety_stock = Z_SAFETY * demand_std * (lead_time ** 0.5)

    # 2024年1月の予測（日別）
    forecast_start = date(2024, 1, 1)
    forecast_dates = [forecast_start + timedelta(days=i) for i in range(FCAST_DAYS)]
    total_forecast = sum(
        base_demand * weekday_factors[fd.weekday()] * trend_factor
        for fd in forecast_dates
    )

    # 推奨発注量（月次需要 + 安全在庫 - 現在庫）
    recommended_order = max(0.0, total_forecast + safety_stock - current_stock)

    # 欠品リスク（現在庫がリードタイム中需要 + 安全在庫を下回る）
    lt_demand = base_demand * LEAD_TIME
    stockout_risk = current_stock < (lt_demand + safety_stock)

    # 過剰在庫（現在庫 / 日次需要 > threshold 日）
    days_of_stock = current_stock / max(base_demand, 0.1)
    overstock = days_of_stock > OVERSTOCK_TH

    row = {
        "product_id": prod_id,
        "product_name": prod_name,
        "category": cat,
        "avg_daily_sales": round(base_demand, 2),
        "trend_factor": round(trend_factor, 3),
        "current_stock": int(current_stock),
        "safety_stock": round(safety_stock, 1),
        "forecast_31days": round(total_forecast, 1),
        "recommended_order": round(recommended_order, 1),
        "days_of_stock": round(days_of_stock, 1),
        "stockout_risk": stockout_risk,
        "overstock": overstock,
    }
    forecast_rows.append(row)
    if stockout_risk:
        stockout_ids.append(prod_id)
    if overstock:
        overstock_ids.append(prod_id)

forecast_df = pd.DataFrame(forecast_rows)
forecast_df.to_csv(OUTPUT_DIR / "forecast_202401.csv",
                   index=False, encoding="utf-8-sig")

# ── レポート生成 ──────────────────────────────────────────────────────
lines = []
lines.append("# 発注最適化・需要予測レポート（2024年1月）\n")
lines.append(f"分析対象商品数: **{len(forecast_df)}商品**  ")
lines.append(f"欠品リスク件数: **{len(stockout_ids)}件**  ")
lines.append(f"過剰在庫件数: **{len(overstock_ids)}件**\n")

# 1. 需要予測サマリー
lines.append("## 需要予測サマリー（カテゴリ別）\n")
cat_summary = forecast_df.groupby("category").agg(
    商品数=("product_id", "count"),
    平均日次販売数=("avg_daily_sales", "mean"),
    月次予測需要合計=("forecast_31days", "sum"),
    推奨発注量合計=("recommended_order", "sum"),
).round(1)
lines.append(cat_summary.to_markdown())
lines.append("")

# 2. 欠品リスク商品リスト
lines.append("## 欠品リスク商品リスト（緊急発注推奨）\n")
stockout_df = forecast_df[forecast_df["stockout_risk"]].sort_values(
    "days_of_stock").head(20)
if len(stockout_df) > 0:
    cols = ["product_id", "product_name", "category",
            "current_stock", "avg_daily_sales", "recommended_order", "days_of_stock"]
    lines.append(stockout_df[cols].to_markdown(index=False))
else:
    lines.append("欠品リスク商品はありません。")
lines.append("")

# 3. 過剰在庫商品リスト
lines.append("## 過剰在庫商品リスト（発注停止推奨）\n")
overstock_df = forecast_df[forecast_df["overstock"]].sort_values(
    "days_of_stock", ascending=False).head(20)
if len(overstock_df) > 0:
    cols = ["product_id", "product_name", "category",
            "current_stock", "avg_daily_sales", "days_of_stock"]
    lines.append(overstock_df[cols].to_markdown(index=False))
else:
    lines.append("過剰在庫商品はありません。")
lines.append("")

# 4. カテゴリ別KPI
lines.append("## カテゴリ別KPI\n")
kpi = forecast_df.groupby("category").agg(
    欠品リスク件数=("stockout_risk", "sum"),
    過剰在庫件数=("overstock", "sum"),
    平均在庫日数=("days_of_stock", "mean"),
).round(1)
lines.append(kpi.to_markdown())
lines.append("")

# 5. ビジネスインサイト
lines.append("## ビジネスインサイト\n")
total_order = forecast_df["recommended_order"].sum()
total_forecast_demand = forecast_df["forecast_31days"].sum()
lines.append(f"- **月次総予測需要**: {total_forecast_demand:,.0f} 個")
lines.append(f"- **月次総推奨発注量**: {total_order:,.0f} 個")
lines.append(f"- **欠品リスク率**: {len(stockout_ids)/len(forecast_df)*100:.1f}%"
             f"（{len(stockout_ids)}/{len(forecast_df)}商品）")
lines.append(f"- **過剰在庫率**: {len(overstock_ids)/len(forecast_df)*100:.1f}%"
             f"（{len(overstock_ids)}/{len(forecast_df)}商品）")
lines.append("")
lines.append("### 発注最適化の重点商品と推奨アクション\n")
# 欠品リスクTOP3
if stockout_ids:
    top_stockout = forecast_df[forecast_df["stockout_risk"]].nsmallest(3, "days_of_stock")
    lines.append("**緊急発注が必要な商品（在庫日数が少ない順）:**")
    for _, row in top_stockout.iterrows():
        lines.append(f"- {row['product_name']}（{row['category']}）: "
                     f"現在庫{row['current_stock']}個、推奨発注量{row['recommended_order']:.0f}個")
lines.append("")
# 過剰在庫TOP3
if overstock_ids:
    top_overstock = forecast_df[forecast_df["overstock"]].nlargest(3, "days_of_stock")
    lines.append("**発注停止を推奨する商品（在庫日数が多い順）:**")
    for _, row in top_overstock.iterrows():
        lines.append(f"- {row['product_name']}（{row['category']}）: "
                     f"在庫日数{row['days_of_stock']:.0f}日分")
lines.append("")
lines.append("### 発注最適化アラート\n")
lines.append(f"欠品リスク商品が{len(stockout_ids)}件検出されました。"
             "リードタイム中の需要＋安全在庫を下回る在庫水準のため、早急な発注手配が必要です。")

report_text = "\n".join(lines)
(OUTPUT_DIR / "analysis_report.md").write_text(report_text, encoding="utf-8")

print(f"分析完了: {len(forecast_df)}商品")
print(f"  欠品リスク: {len(stockout_ids)}件")
print(f"  過剰在庫: {len(overstock_ids)}件")
print(f"  月次総予測需要: {total_forecast_demand:,.0f}")
print(f"  月次総推奨発注量: {total_order:,.0f}")
print("forecast_202401.csv, analysis_report.md を出力しました")

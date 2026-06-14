import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path("C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/05_logistics/01_inventory")
OUTPUT_DIR = BASE_DIR / "output"

STOCKOUT_THRESHOLD = 0
LOW_STOCK_RATIO_THRESHOLD = 0.20

df = pd.read_csv(OUTPUT_DIR / "cleaned_inventory_202401.csv", encoding="utf-8-sig")

for col in ["stock_qty", "min_stock_qty", "unit_cost", "received_qty", "shipped_qty"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

df["stockout_flag"] = df["stock_qty"] < df["min_stock_qty"]
df["stock_value"] = df["stock_qty"] * df["unit_cost"]
df["turnover_rate"] = df.apply(
    lambda r: r["shipped_qty"] / r["stock_qty"] if r["stock_qty"] > 0 else 0.0,
    axis=1,
)

lines = ["# 在庫データ分析レポート（2024年1月）\n"]

lines.append("## 1. 倉庫別在庫サマリー\n")
wh_summary = df.groupby("warehouse").agg(
    在庫金額合計=("stock_value", "sum"),
    平均在庫数=("stock_qty", "mean"),
    品目数=("item_code", "nunique"),
).sort_values("在庫金額合計", ascending=False)
wh_fmt = wh_summary.copy()
wh_fmt["在庫金額合計"] = wh_fmt["在庫金額合計"].map("{:,.0f}円".format)
wh_fmt["平均在庫数"] = wh_fmt["平均在庫数"].map("{:.1f}".format)
lines.append(wh_fmt.to_markdown())
lines.append("")

lines.append("## 2. 欠品検知\n")
stockout_df = df[df["stockout_flag"]].copy()
total_items = len(df)
stockout_count = int(df["stockout_flag"].sum())
stockout_ratio = stockout_count / total_items * 100 if total_items > 0 else 0

lines.append(f"- 欠品品目数: **{stockout_count}件** / {total_items}件 ({stockout_ratio:.1f}%)")
if stockout_ratio > LOW_STOCK_RATIO_THRESHOLD * 100:
    lines.append(f"- **アラート: 欠品率 {stockout_ratio:.1f}% が閾値 {LOW_STOCK_RATIO_THRESHOLD*100:.0f}% を超過**")
else:
    lines.append(f"- 欠品率 {stockout_ratio:.1f}% は閾値（{LOW_STOCK_RATIO_THRESHOLD*100:.0f}%）以内で正常範囲です")
lines.append("")

if stockout_count > 0:
    lines.append("### 欠品品目一覧（在庫数量 < 最低在庫数）\n")
    show_cols = [c for c in ["warehouse", "item_code", "item_name", "category",
                              "stock_qty", "min_stock_qty"] if c in stockout_df.columns]
    lines.append(stockout_df[show_cols].to_markdown(index=False))
    lines.append("")

lines.append("## 3. 倉庫別欠品品目数\n")
stockout_by_wh = df.groupby("warehouse")["stockout_flag"].sum().sort_values(ascending=False)
for wh, cnt in stockout_by_wh.items():
    lines.append(f"- {wh}: {int(cnt)}件")
lines.append("")

lines.append("## 4. 在庫回転率分析\n")
turnover_summary = df.groupby("category")["turnover_rate"].agg(
    平均回転率="mean",
    最大回転率="max",
    最小回転率="min",
).sort_values("平均回転率", ascending=False)
lines.append(turnover_summary.round(3).to_markdown())
lines.append("")

lines.append("## 5. 異常値検出（±2σ）\n")
anomalies = []
if "date" in df.columns:
    daily_value = df.groupby(["warehouse", "date"])["stock_value"].sum().reset_index()
    for wh, grp in daily_value.groupby("warehouse"):
        if len(grp) > 2:
            mean = grp["stock_value"].mean()
            std = grp["stock_value"].std()
            if std > 0:
                outliers = grp[np.abs(grp["stock_value"] - mean) > 2 * std]
                for _, row in outliers.iterrows():
                    date_str = str(row["date"])[:10]
                    anomalies.append(
                        f"- {wh} | {date_str} | {row['stock_value']:,.0f}円"
                        f"（平均 {mean:,.0f}円 から {(row['stock_value']-mean)/std:+.1f}σ）"
                    )
if anomalies:
    lines.extend(anomalies)
else:
    lines.append("- 異常値は検出されませんでした")
lines.append("")

lines.append("## 6. ビジネスインサイト\n")
total_stock_value = df["stock_value"].sum()
wh_totals = df.groupby("warehouse")["stock_value"].sum()
top_wh = wh_totals.idxmax()
bottom_wh = wh_totals.idxmin()
lines.append(f"- 総在庫金額: **{total_stock_value:,.0f}円**")
lines.append(f"- 在庫金額最大倉庫: **{top_wh}**（{wh_totals[top_wh]:,.0f}円）")
lines.append(f"- 在庫金額最小倉庫: **{bottom_wh}**（{wh_totals[bottom_wh]:,.0f}円）")
if stockout_count > 0:
    lines.append(f"- 欠品品目 {stockout_count} 件が検出されました — 緊急発注を検討してください")
if anomalies:
    lines.append(f"- 在庫金額の異常値が {len(anomalies)} 件検出されました — 要因調査を推奨")
lines.append("")

(OUTPUT_DIR / "analysis_report.md").write_text("\n".join(lines), encoding="utf-8")
print("分析完了: output/analysis_report.md を生成しました")

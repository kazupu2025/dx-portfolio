import pandas as pd
import numpy as np
from pathlib import Path
import yaml

with open("config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

WASTE_ALERT = config.get("waste_rate_alert_threshold", 0.10)
HIGH_COST   = config.get("high_cost_alert_threshold", 50000)

df = pd.read_csv("output/cleaned_cost_202401.csv", encoding="utf-8-sig")
for col in ["purchase_qty", "unit_cost", "used_qty", "waste_qty",
            "purchase_cost", "waste_cost", "waste_rate"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

lines = ["# 原価管理・食材ロス分析レポート（2024年1月）\n"]

# 1. カテゴリ別仕入コストサマリー
lines.append("## 1. カテゴリ別仕入コストサマリー\n")
cat_summary = df.groupby("category").agg(
    仕入コスト合計=("purchase_cost", "sum"),
    廃棄コスト合計=("waste_cost",    "sum"),
    仕入量合計=("purchase_qty", "sum"),
    廃棄量合計=("waste_qty",    "sum"),
).copy()
cat_summary["ロス率(%)"] = (cat_summary["廃棄量合計"] / cat_summary["仕入量合計"].replace(0, 1) * 100).round(2)
cat_summary["廃棄コスト率(%)"] = (cat_summary["廃棄コスト合計"] / cat_summary["仕入コスト合計"].replace(0, 1) * 100).round(2)
cat_summary["アラート"] = cat_summary["ロス率(%)"].apply(
    lambda x: "要対応" if x > WASTE_ALERT * 100 else "正常"
)
cat_summary = cat_summary.sort_values("仕入コスト合計", ascending=False)
fmt = cat_summary.copy()
fmt["仕入コスト合計"] = fmt["仕入コスト合計"].map("{:,.0f}円".format)
fmt["廃棄コスト合計"] = fmt["廃棄コスト合計"].map("{:,.0f}円".format)
lines.append(fmt.to_markdown())
lines.append("")

# 2. 店舗別食材ロス率アラート
lines.append("## 2. 店舗別食材ロス率\n")
store_summary = df.groupby("store").agg(
    仕入コスト合計=("purchase_cost", "sum"),
    廃棄コスト合計=("waste_cost",    "sum"),
    平均ロス率=("waste_rate", "mean"),
).copy()
store_summary["平均ロス率(%)"] = (store_summary["平均ロス率"] * 100).round(2)
store_summary["アラート"] = store_summary["平均ロス率(%)"].apply(
    lambda x: "要改善" if x > WASTE_ALERT * 100 else "正常"
)
store_summary = store_summary.drop(columns="平均ロス率").sort_values("平均ロス率(%)", ascending=False)
fmt2 = store_summary.copy()
fmt2["仕入コスト合計"] = fmt2["仕入コスト合計"].map("{:,.0f}円".format)
fmt2["廃棄コスト合計"] = fmt2["廃棄コスト合計"].map("{:,.0f}円".format)
lines.append(fmt2.to_markdown())
lines.append("")

# 3. 廃棄コスト上位食材 TOP10
lines.append("## 3. 廃棄コスト上位食材 TOP10\n")
ing_summary = df.groupby(["ingredient_code", "ingredient_name", "category"]).agg(
    廃棄コスト合計=("waste_cost",  "sum"),
    ロス率平均=("waste_rate", "mean"),
    仕入コスト合計=("purchase_cost", "sum"),
).copy()
ing_summary["ロス率平均(%)"] = (ing_summary["ロス率平均"] * 100).round(2)
ing_summary = ing_summary.drop(columns="ロス率平均").sort_values("廃棄コスト合計", ascending=False).head(10)
fmt3 = ing_summary.copy()
fmt3["廃棄コスト合計"] = fmt3["廃棄コスト合計"].map("{:,.0f}円".format)
fmt3["仕入コスト合計"] = fmt3["仕入コスト合計"].map("{:,.0f}円".format)
lines.append(fmt3.to_markdown())
lines.append("")

# 4. 日次廃棄コストトレンド
lines.append("## 4. 日次廃棄コストトレンド\n")
if "date" in df.columns:
    daily = df.groupby("date").agg(
        仕入コスト=("purchase_cost", "sum"),
        廃棄コスト=("waste_cost", "sum"),
    ).copy()
    daily["ロス率(%)"] = (daily["廃棄コスト"] / daily["仕入コスト"].replace(0, 1) * 100).round(2)
    peak_date = daily["廃棄コスト"].idxmax()
    avg_daily_waste = daily["廃棄コスト"].mean()
    lines.append(f"- 日次平均廃棄コスト: **{avg_daily_waste:,.0f}円**")
    lines.append(f"- 廃棄コスト最大日: {str(peak_date)[:10]}（{daily.loc[peak_date,'廃棄コスト']:,.0f}円）")
lines.append("")

# 5. 高廃棄ロス検出
lines.append("## 5. 高廃棄ロス検出\n")
high_waste = df[df["waste_rate"] > WASTE_ALERT]
if len(high_waste) > 0:
    hw_summary = high_waste.groupby(["ingredient_name", "store"]).agg(
        件数=("waste_rate", "count"),
        平均ロス率=("waste_rate", "mean"),
        廃棄コスト合計=("waste_cost", "sum"),
    ).sort_values("廃棄コスト合計", ascending=False).head(10)
    hw_summary["平均ロス率(%)"] = (hw_summary["平均ロス率"] * 100).round(1)
    hw_summary = hw_summary.drop(columns="平均ロス率")
    lines.append(f"**ロス率{WASTE_ALERT*100:.0f}%超の高廃棄ロス: {len(high_waste)}件**")
    lines.append(hw_summary.to_markdown())
else:
    lines.append(f"- ロス率{WASTE_ALERT*100:.0f}%超の高廃棄ロスは検出されませんでした")
lines.append("")

# 6. ビジネスインサイト
lines.append("## 6. ビジネスインサイト\n")
total_purchase = df["purchase_cost"].sum()
total_waste    = df["waste_cost"].sum()
overall_loss   = total_waste / total_purchase * 100 if total_purchase > 0 else 0
worst_cat   = cat_summary["ロス率(%)"].idxmax()  if not cat_summary.empty else "不明"
worst_store = store_summary["平均ロス率(%)"].idxmax() if not store_summary.empty else "不明"
alert_cats  = cat_summary[cat_summary["ロス率(%)"] > WASTE_ALERT * 100]
alert_stores= store_summary[store_summary["平均ロス率(%)"] > WASTE_ALERT * 100]

lines.append(f"- 月次総仕入コスト: **{total_purchase:,.0f}円**")
lines.append(f"- 月次総廃棄コスト: **{total_waste:,.0f}円**（ロス率: {overall_loss:.2f}%）")
lines.append(f"- ロス率最高カテゴリ: **{worst_cat}**")
lines.append(f"- ロス率最高店舗: **{worst_store}**")
if len(alert_cats) > 0:
    lines.append(f"- **{len(alert_cats)}カテゴリがロス率{WASTE_ALERT*100:.0f}%超 — 発注量の見直しが必要です**")
if len(alert_stores) > 0:
    lines.append(f"- **{len(alert_stores)}店舗がロス率{WASTE_ALERT*100:.0f}%超 — 調理・保管方法の改善を検討してください**")
lines.append("")

Path("output/analysis_report.md").write_text("\n".join(lines), encoding="utf-8")
print(f"分析完了: 仕入{total_purchase:,.0f}円, 廃棄{total_waste:,.0f}円, ロス率{overall_loss:.2f}%")

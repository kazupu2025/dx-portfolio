import pandas as pd
import numpy as np
import yaml
from pathlib import Path

with open("config.yml", encoding="utf-8") as _f:
    _config = yaml.safe_load(_f)
WASTE_ALERT_THRESHOLD = _config.get("waste_loss_alert_threshold", 0.05)

df = pd.read_csv("output/cleaned_sales_202401.csv", encoding="utf-8-sig")

if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
for col in ["sales_amount", "waste_qty", "waste_amount"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

lines = ["# 売上・廃棄ロス分析レポート（2024年1月）\n"]

# 1. 店舗別サマリー
lines.append("## 1. 店舗別サマリー\n")
store_summary = df.groupby("store_name")["sales_amount"].agg(
    月間合計="sum", 日平均="mean", 最高日売上="max", 最低日売上="min"
).sort_values("月間合計", ascending=False)
store_summary_fmt = store_summary.copy()
store_summary_fmt["月間合計"] = store_summary_fmt["月間合計"].map("{:,.0f}円".format)
store_summary_fmt["日平均"] = store_summary_fmt["日平均"].map("{:,.0f}円".format)
lines.append(store_summary_fmt.to_markdown())
lines.append("")

# 2. 月間売上ランキング
lines.append("## 2. 月間売上ランキング\n")
ranking = df.groupby("store_name")["sales_amount"].sum().sort_values(ascending=False).reset_index()
for i, row in ranking.iterrows():
    lines.append(f"{i+1}. {row['store_name']}: {row['sales_amount']:,.0f}円")
lines.append("")

# 3. 日次トレンド
if "date" in df.columns:
    lines.append("## 3. 日次トレンド\n")
    daily = df.groupby("date")["sales_amount"].sum()
    if len(daily) >= 20:
        first10 = daily.iloc[:10].mean()
        last10 = daily.iloc[-10:].mean()
        change = (last10 - first10) / first10 * 100 if first10 > 0 else 0
        lines.append(f"- 月初10日平均: {first10:,.0f}円")
        lines.append(f"- 月末10日平均: {last10:,.0f}円")
        lines.append(f"- 月初→月末変化率: {change:+.1f}%")
    lines.append("")

# 4. 異常値検出（±2σ）
lines.append("## 4. 異常値検出（±2σ）\n")
anomalies = []
if "date" in df.columns:
    daily_store = df.groupby(["store_name", "date"])["sales_amount"].sum().reset_index()
    for store, grp in daily_store.groupby("store_name"):
        if len(grp) > 2:
            mean = grp["sales_amount"].mean()
            std = grp["sales_amount"].std()
            if std > 0:
                outliers = grp[np.abs(grp["sales_amount"] - mean) > 2 * std]
                for _, row in outliers.iterrows():
                    date_str = str(row.get("date", "不明"))[:10]
                    anomalies.append(
                        f"- {store} | {date_str} | {row['sales_amount']:,.0f}円"
                        f"（日次合計平均 {mean:,.0f}円 から {(row['sales_amount']-mean)/std:+.1f}σ）"
                    )
if anomalies:
    lines.extend(anomalies)
else:
    lines.append("- 異常値は検出されませんでした")
lines.append("")

# 5. ビジネスインサイト
lines.append("## 5. ビジネスインサイト\n")
total = df["sales_amount"].sum()
store_totals = df.groupby("store_name")["sales_amount"].sum()
top_store = store_totals.idxmax()
bottom_store = store_totals.idxmin()
top_val = store_totals.max()
bottom_val = store_totals.min()
gap_ratio = top_val / bottom_val if bottom_val > 0 else float("inf")

lines.append(f"- 全店舗1月合計売上: **{total:,.0f}円**")
lines.append(f"- トップ店舗: **{top_store}**（{top_val:,.0f}円）")
lines.append(f"- ボトム店舗: **{bottom_store}**（{bottom_val:,.0f}円）")
lines.append(f"- トップ/ボトム倍率: **{gap_ratio:.1f}倍** — {'格差が大きい' if gap_ratio > 2 else '均衡している'}")
if anomalies:
    lines.append(f"- 異常値が {len(anomalies)} 件検出 — 要因調査を推奨")
lines.append("")

# 6. 廃棄ロス率分析（A-02 追加）
lines.append("## 6. 廃棄ロス率分析\n")
if "waste_amount" in df.columns and "sales_amount" in df.columns:
    agg_dict = {"売上合計": ("sales_amount", "sum"), "廃棄金額合計": ("waste_amount", "sum")}
    if "waste_qty" in df.columns:
        agg_dict["廃棄数量合計"] = ("waste_qty", "sum")
    waste_summary = df.groupby("store_name").agg(**agg_dict)
    waste_summary["廃棄ロス率"] = (
        waste_summary["廃棄金額合計"] / waste_summary["売上合計"] * 100
    ).fillna(0)
    waste_summary_fmt = waste_summary.copy()
    waste_summary_fmt["売上合計"] = waste_summary_fmt["売上合計"].map("{:,.0f}円".format)
    waste_summary_fmt["廃棄金額合計"] = waste_summary_fmt["廃棄金額合計"].map("{:,.0f}円".format)
    waste_summary_fmt["廃棄ロス率"] = waste_summary_fmt["廃棄ロス率"].map("{:.2f}%".format)
    lines.append(waste_summary_fmt.to_markdown())
    lines.append("")

    alert_stores = waste_summary[waste_summary["廃棄ロス率"] > WASTE_ALERT_THRESHOLD * 100]
    if len(alert_stores) > 0:
        lines.append(f"### アラート: 廃棄ロス率 {WASTE_ALERT_THRESHOLD*100:.0f}% 超の店舗")
        for store, row in alert_stores.iterrows():
            lines.append(
                f"- **{store}**: 廃棄ロス率 {row['廃棄ロス率']:.2f}% "
                f"（廃棄金額: {row['廃棄金額合計']:,.0f}円）"
            )
        lines.append("")
    else:
        lines.append(f"- 全店舗の廃棄ロス率は {WASTE_ALERT_THRESHOLD*100:.0f}% 以内で正常範囲です")
        lines.append("")

    if "category" in df.columns:
        lines.append("### カテゴリ別廃棄ロス率\n")
        cat_waste = df.groupby("category").agg(
            売上=("sales_amount", "sum"),
            廃棄=("waste_amount", "sum"),
        )
        cat_waste["廃棄ロス率"] = (cat_waste["廃棄"] / cat_waste["売上"] * 100).fillna(0)
        cat_waste = cat_waste.sort_values("廃棄ロス率", ascending=False)
        cat_waste_fmt = cat_waste.copy()
        cat_waste_fmt["廃棄ロス率"] = cat_waste_fmt["廃棄ロス率"].map("{:.2f}%".format)
        lines.append(cat_waste_fmt.to_markdown())
        lines.append("")
else:
    lines.append("- waste_amount 列が見つからないためスキップ")
    lines.append("")

Path("output/analysis_report.md").write_text("\n".join(lines), encoding="utf-8")
print("分析完了: output/analysis_report.md を生成しました")

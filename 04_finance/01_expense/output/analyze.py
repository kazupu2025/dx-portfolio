import pandas as pd
import numpy as np
from pathlib import Path
import yaml

with open("config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)
BUDGET_ALERT_THRESHOLD = config.get("budget_alert_threshold", 1.0)

df = pd.read_csv("output/cleaned_expense_202401.csv", encoding="utf-8-sig")
for col in ["amount", "budget"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

lines = ["# 経費精算データ分析レポート（2024年1月）\n"]

# 1. 部門別経費サマリー
lines.append("## 1. 部門別経費サマリー\n")
dept_summary = df.groupby("department").agg(
    経費合計=("amount", "sum"),
    予算合計=("budget", "sum"),
    件数=("amount", "count"),
).sort_values("経費合計", ascending=False)
dept_summary["予算消化率(%)"] = (dept_summary["経費合計"] / dept_summary["予算合計"].replace(0, 1) * 100).round(1)
dept_summary["アラート"] = dept_summary["予算消化率(%)"].apply(
    lambda x: "⚠ 超過" if x > BUDGET_ALERT_THRESHOLD * 100 else "正常"
)
fmt = dept_summary.copy()
fmt["経費合計"] = fmt["経費合計"].map("{:,.0f}円".format)
fmt["予算合計"] = fmt["予算合計"].map("{:,.0f}円".format)
lines.append(fmt.to_markdown())
lines.append("")

# 2. 予算超過検知
lines.append("## 2. 予算超過検知\n")
over_depts = dept_summary[dept_summary["予算消化率(%)"] > BUDGET_ALERT_THRESHOLD * 100]
if len(over_depts) > 0:
    lines.append(f"- **アラート: {len(over_depts)}部門が予算超過**")
    for dept, row in over_depts.iterrows():
        lines.append(f"  - {dept}: {row['予算消化率(%)']:.1f}%（予算の{row['予算消化率(%)']:.1f}%を消化）")
else:
    lines.append(f"- 全部門が予算内（閾値: {BUDGET_ALERT_THRESHOLD*100:.0f}%）")
lines.append("")

# 3. 費目別経費サマリー
lines.append("## 3. 費目別経費サマリー\n")
type_summary = df.groupby("expense_type").agg(
    経費合計=("amount", "sum"),
    件数=("amount", "count"),
    平均金額=("amount", "mean"),
).sort_values("経費合計", ascending=False)
fmt2 = type_summary.copy()
fmt2["経費合計"] = fmt2["経費合計"].map("{:,.0f}円".format)
fmt2["平均金額"] = fmt2["平均金額"].map("{:,.0f}円".format)
lines.append(fmt2.to_markdown())
lines.append("")

# 4. 日次経費トレンド（上位3部門）
lines.append("## 4. 日次経費トレンド\n")
if "date" in df.columns:
    top_depts = dept_summary.head(3).index.tolist()
    daily = df[df["department"].isin(top_depts)].groupby(["department", "date"])["amount"].sum().reset_index()
    for dept in top_depts:
        dept_data = daily[daily["department"] == dept]
        if len(dept_data) > 0:
            total = dept_data["amount"].sum()
            lines.append(f"- {dept}: 月計 {total:,.0f}円 ({len(dept_data)}営業日)")
lines.append("")

# 5. 異常値検出（部門×日次経費 ±2σ）
lines.append("## 5. 異常値検出（±2σ）\n")
anomalies = []
if "date" in df.columns:
    daily_dept = df.groupby(["department", "date"])["amount"].sum().reset_index()
    for dept, grp in daily_dept.groupby("department"):
        if len(grp) > 2:
            mean = grp["amount"].mean()
            std = grp["amount"].std()
            if std > 0:
                outliers = grp[np.abs(grp["amount"] - mean) > 2 * std]
                for _, row in outliers.iterrows():
                    date_str = str(row["date"])[:10]
                    anomalies.append(
                        f"- {dept} | {date_str} | {row['amount']:,.0f}円"
                        f"（平均 {mean:,.0f}円 から {(row['amount']-mean)/std:+.1f}σ）"
                    )
if anomalies:
    lines.extend(anomalies)
else:
    lines.append("- 異常値は検出されませんでした")
lines.append("")

# 6. ビジネスインサイト
lines.append("## 6. ビジネスインサイト\n")
total_amount = df["amount"].sum()
total_budget = df["budget"].sum()
budget_ratio = total_amount / total_budget * 100 if total_budget > 0 else 0
top_dept = dept_summary["経費合計"].idxmax()
top_type = type_summary["経費合計"].idxmax()
lines.append(f"- 総経費: **{total_amount:,.0f}円**（予算消化率: {budget_ratio:.1f}%）")
lines.append(f"- 経費最多部門: **{top_dept}**")
lines.append(f"- 最多費目: **{top_type}**")
if len(over_depts) > 0:
    lines.append(f"- **{len(over_depts)}部門が予算超過 — 翌月の経費計画を見直してください**")
if anomalies:
    lines.append(f"- 異常値 {len(anomalies)} 件検出 — 高額経費の承認状況を確認してください")
lines.append("")

Path("output/analysis_report.md").write_text("\n".join(lines), encoding="utf-8")
print("分析完了: output/analysis_report.md を生成しました")

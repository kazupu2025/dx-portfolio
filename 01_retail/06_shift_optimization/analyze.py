# -*- coding: utf-8 -*-
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CSV_PATH = os.path.join(OUTPUT_DIR, "cleaned_shift_202401.csv")
df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
df["shift_date"] = pd.to_datetime(df["shift_date"], format="%Y-%m-%d")

# Store summary
store_summary = df.groupby("store_name").agg(
    total_labor_cost=("daily_wage", "sum"),
    avg_fill_rate=("actual_staff", lambda x: (x / df.loc[x.index, "required_staff"]).mean()),
    understaffed_count=("is_understaffed", "sum"),
).reset_index()
store_summary["avg_fill_rate"] = store_summary["avg_fill_rate"].round(3)
store_summary = store_summary.sort_values("total_labor_cost", ascending=False)

store_summary_path = os.path.join(OUTPUT_DIR, "store_summary_202401.csv")
store_summary.to_csv(store_summary_path, index=False, encoding="utf-8-sig")
print(f"[OK] store_summary saved: {store_summary_path}")

# Role summary
role_summary = df.groupby("role").agg(
    avg_hourly_rate=("hourly_rate", "mean"),
    avg_required_staff=("required_staff", "mean"),
).reset_index()
role_summary["avg_hourly_rate"] = role_summary["avg_hourly_rate"].round(1)
role_summary["avg_required_staff"] = role_summary["avg_required_staff"].round(2)

# Daily trend
daily_trend = df.groupby("shift_date").agg(
    total_daily_wage=("daily_wage", "sum"),
).reset_index()
daily_trend["shift_date"] = daily_trend["shift_date"].dt.strftime("%Y-%m-%d")
daily_trend = daily_trend.sort_values("shift_date")

# Overall stats
total_cost = int(df["daily_wage"].sum())
total_understaffed = int(df["is_understaffed"].sum())
overall_fill_rate = (df["actual_staff"] / df["required_staff"]).mean()

# Write markdown report
report_path = os.path.join(OUTPUT_DIR, "analysis_report.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("# シフト充足率・人件費最適化レポート\n\n")
    f.write("## 分析期間: 2024-01-01 〜 2024-01-20\n\n")

    f.write("## 全体サマリー\n\n")
    f.write(f"- 総人件費: {total_cost:,} 円\n")
    f.write(f"- 不足シフト件数: {total_understaffed} 件\n")
    f.write(f"- 平均充足率: {overall_fill_rate:.3f}\n\n")

    f.write("## 店舗別サマリー\n\n")
    f.write("| 店舗名 | 総人件費 | 平均充足率 | 不足シフト件数 |\n")
    f.write("|--------|----------|------------|----------------|\n")
    for _, row in store_summary.iterrows():
        f.write(f"| {row['store_name']} | {int(row['total_labor_cost']):,} | {row['avg_fill_rate']:.3f} | {int(row['understaffed_count'])} |\n")

    f.write("\n## 役割別サマリー\n\n")
    f.write("| 役割 | 平均時給 | 平均必要人員 |\n")
    f.write("|------|----------|-------------|\n")
    for _, row in role_summary.iterrows():
        f.write(f"| {row['role']} | {row['avg_hourly_rate']:.1f} | {row['avg_required_staff']:.2f} |\n")

    f.write("\n## 日別人件費トレンド\n\n")
    f.write("| 日付 | 総人件費 |\n")
    f.write("|------|----------|\n")
    for _, row in daily_trend.iterrows():
        f.write(f"| {row['shift_date']} | {int(row['total_daily_wage']):,} |\n")

print(f"[OK] analysis_report.md saved: {report_path}")
print("[OK] analyze.py completed")

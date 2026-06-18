# -*- coding: utf-8 -*-
import os
import pandas as pd
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CLEANED_FILE = os.path.join(OUTPUT_DIR, "cleaned_attendance_202401.csv")

df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")

# --- Analysis 1: By staff type ---
staff_summary = df.groupby("staff_type").agg(
    total_records=("record_id", "count"),
    absent_count=("is_absent", "sum"),
    avg_overtime_hours=("overtime_hours", "mean"),
    avg_utilization_rate=("utilization_rate", "mean"),
).reset_index()

staff_summary["attendance_rate"] = (
    (staff_summary["total_records"] - staff_summary["absent_count"])
    / staff_summary["total_records"]
).round(4)
staff_summary["avg_overtime_hours"] = staff_summary["avg_overtime_hours"].round(2)
staff_summary["avg_utilization_rate"] = staff_summary["avg_utilization_rate"].round(4)

# --- Analysis 2: By department ---
dept_summary = df.groupby("department").agg(
    total_records=("record_id", "count"),
    absent_count=("is_absent", "sum"),
    avg_utilization_rate=("utilization_rate", "mean"),
).reset_index()
dept_summary["attendance_rate"] = (
    (dept_summary["total_records"] - dept_summary["absent_count"])
    / dept_summary["total_records"]
).round(4)
dept_summary["avg_utilization_rate"] = dept_summary["avg_utilization_rate"].round(4)

# --- Overall KPIs ---
total_records = len(df)
attendance_count = (df["is_absent"] == 0).sum()
absent_count = (df["is_absent"] == 1).sum()
overall_attendance_rate = round(attendance_count / total_records, 4)
avg_utilization_rate = round(df["utilization_rate"].mean(), 4)
avg_overtime_hours = round(df["overtime_hours"].mean(), 2)
overtime_count = (df["overtime_hours"] > 0).sum()

# --- Output staff_summary CSV ---
staff_csv_path = os.path.join(OUTPUT_DIR, "staff_summary_202401.csv")
staff_summary.to_csv(staff_csv_path, index=False, encoding="utf-8-sig")
print("[OK] staff_summary saved: {}".format(staff_csv_path))

# --- Output analysis_report.md ---
report_lines = []
report_lines.append("# 医療スタッフ勤怠・稼働率分析レポート")
report_lines.append("")
report_lines.append("## 概要")
report_lines.append("")
report_lines.append("- 総勤務記録数: {}件".format(total_records))
report_lines.append("- 出勤件数: {}件".format(attendance_count))
report_lines.append("- 欠勤件数: {}件".format(absent_count))
report_lines.append("- 出勤率: {:.1%}".format(overall_attendance_rate))
report_lines.append("- 平均稼働率: {:.1%}".format(avg_utilization_rate))
report_lines.append("- 平均残業時間: {}時間".format(avg_overtime_hours))
report_lines.append("- 残業件数: {}件".format(int(overtime_count)))
report_lines.append("")
report_lines.append("## スタッフ種別別集計")
report_lines.append("")
report_lines.append("| スタッフ種別 | 総記録数 | 欠勤件数 | 出勤率 | 平均稼働率 | 平均残業時間 |")
report_lines.append("|------------|--------|--------|------|--------|-----------|")
for _, row in staff_summary.iterrows():
    report_lines.append("| {} | {} | {} | {:.1%} | {:.1%} | {}h |".format(
        row["staff_type"],
        int(row["total_records"]),
        int(row["absent_count"]),
        row["attendance_rate"],
        row["avg_utilization_rate"],
        row["avg_overtime_hours"],
    ))
report_lines.append("")
report_lines.append("## 診療科別集計")
report_lines.append("")
report_lines.append("| 診療科 | 総記録数 | 欠勤件数 | 出勤率 | 平均稼働率 |")
report_lines.append("|------|--------|--------|------|--------|")
for _, row in dept_summary.iterrows():
    report_lines.append("| {} | {} | {} | {:.1%} | {:.1%} |".format(
        row["department"],
        int(row["total_records"]),
        int(row["absent_count"]),
        row["attendance_rate"],
        row["avg_utilization_rate"],
    ))

report_path = os.path.join(OUTPUT_DIR, "analysis_report.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))
print("[OK] analysis_report.md saved: {}".format(report_path))

# --- Output result JSON ---
result = {
    "total_records": int(total_records),
    "attendance_count": int(attendance_count),
    "absent_count": int(absent_count),
    "overall_attendance_rate": float(overall_attendance_rate),
    "avg_utilization_rate": float(avg_utilization_rate),
    "avg_overtime_hours": float(avg_overtime_hours),
    "overtime_count": int(overtime_count),
}
result_path = os.path.join(OUTPUT_DIR, "result_analysis.json")
with open(result_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("[OK] result_analysis.json saved: {}".format(result_path))

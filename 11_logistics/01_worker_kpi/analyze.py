# -*- coding: utf-8 -*-
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CSV_PATH = os.path.join(OUTPUT_DIR, "cleaned_worker_kpi_202401.csv")

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# --- Worker summary ---
worker_summary = df.groupby("worker_id").agg(
    avg_throughput=("throughput", "mean"),
    avg_error_rate=("error_rate", "mean"),
).reset_index()

# KPI flag: majority vote per worker
kpi_mode = df.groupby("worker_id")["kpi_flag"].agg(
    lambda x: x.value_counts().index[0]
).reset_index().rename(columns={"kpi_flag": "kpi_flag"})
worker_summary = worker_summary.merge(kpi_mode, on="worker_id")
worker_summary["avg_throughput"] = worker_summary["avg_throughput"].round(2)
worker_summary["avg_error_rate"] = worker_summary["avg_error_rate"].round(4)

worker_out = os.path.join(OUTPUT_DIR, "worker_summary_202401.csv")
worker_summary.to_csv(worker_out, index=False, encoding="utf-8-sig")
print(f"[OK] Worker summary: {len(worker_summary)} workers -> output/worker_summary_202401.csv")

# --- Zone analysis ---
zone_summary = df.groupby("zone").agg(
    total_processed=("processed_qty", "sum"),
    total_errors=("error_qty", "sum"),
).reset_index()

# --- Task analysis ---
task_summary = df.groupby("task_type").agg(
    avg_work_hours=("work_hours", "mean"),
    total_overtime=("overtime_hours", "sum"),
).reset_index()
task_summary["avg_work_hours"] = task_summary["avg_work_hours"].round(2)
task_summary["total_overtime"] = task_summary["total_overtime"].round(1)

# --- Build report ---
lines = []
lines.append("# Logistics Worker KPI Analysis Report")
lines.append("")
lines.append(f"Analysis period: 2024-01-01 to 2024-01-20")
lines.append(f"Total records: {len(df)}")
lines.append(f"Workers analyzed: {df['worker_id'].nunique()}")
lines.append("")

lines.append("## Worker KPI Summary (Top 5 by Throughput)")
lines.append("")
top5 = worker_summary.sort_values("avg_throughput", ascending=False).head(5)
lines.append("| worker_id | avg_throughput | avg_error_rate | kpi_flag |")
lines.append("|-----------|---------------|----------------|----------|")
for _, row in top5.iterrows():
    lines.append(f"| {row['worker_id']} | {row['avg_throughput']} | {row['avg_error_rate']} | {row['kpi_flag']} |")
lines.append("")

lines.append("## Zone Analysis")
lines.append("")
lines.append("| zone | total_processed | total_errors |")
lines.append("|------|----------------|-------------|")
for _, row in zone_summary.iterrows():
    lines.append(f"| {row['zone']} | {int(row['total_processed'])} | {int(row['total_errors'])} |")
lines.append("")

lines.append("## Task Type Analysis")
lines.append("")
lines.append("| task_type | avg_work_hours | total_overtime |")
lines.append("|-----------|---------------|----------------|")
for _, row in task_summary.iterrows():
    lines.append(f"| {row['task_type']} | {row['avg_work_hours']} | {row['total_overtime']} |")
lines.append("")

lines.append("## KPI Flag Distribution")
lines.append("")
kpi_dist = df["kpi_flag"].value_counts()
for flag, count in kpi_dist.items():
    lines.append(f"- {flag}: {count} records ({count/len(df)*100:.1f}%)")
lines.append("")

report_path = os.path.join(OUTPUT_DIR, "analysis_report.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"[OK] Analysis report -> output/analysis_report.md")
print(f"[OK] Zone summary: {zone_summary['zone'].tolist()}")
print(f"[OK] Task summary: {task_summary['task_type'].tolist()}")

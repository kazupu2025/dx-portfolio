# -*- coding: utf-8 -*-
import os
import pandas as pd

os.makedirs("output", exist_ok=True)

df = pd.read_csv("output/cleaned_progress_202401.csv", encoding="utf-8-sig")

# Site summary
site_summary = df.groupby("site_name").agg(
    avg_progress=("progress_pct", "mean"),
    total_defects=("defect_count", "sum"),
    delayed_count=("is_delayed", "sum")
).reset_index()
site_summary["avg_progress"] = site_summary["avg_progress"].round(2)

# Process summary
process_summary = df.groupby("process").agg(
    avg_efficiency=("efficiency", "mean"),
    problem_kpi_count=("kpi_flag", lambda x: (x == "問題あり").sum())
).reset_index()
process_summary["avg_efficiency"] = process_summary["avg_efficiency"].round(3)

# Worker summary (top 5 by total actual hours)
worker_summary = df.groupby("worker_id").agg(
    total_actual_hours=("actual_hours", "sum"),
    avg_progress=("progress_pct", "mean")
).reset_index()
worker_summary["avg_progress"] = worker_summary["avg_progress"].round(2)
worker_top5 = worker_summary.nlargest(5, "total_actual_hours").reset_index(drop=True)

# Save site_summary CSV
site_summary.to_csv("output/site_summary_202401.csv", index=False, encoding="utf-8-sig")
print("[OK] output/site_summary_202401.csv saved")

# Build markdown report
lines = []
lines.append("# 工程進捗・作業員稼働KPI 分析レポート\n")
lines.append("## 1. 現場別サマリー\n")
lines.append(site_summary.to_markdown(index=False))
lines.append("\n")
lines.append("## 2. 工程別サマリー\n")
lines.append(process_summary.to_markdown(index=False))
lines.append("\n")
lines.append("## 3. 作業員別 累積稼働時間 上位5名\n")
lines.append(worker_top5.to_markdown(index=False))
lines.append("\n")

report = "\n".join(lines)
with open("output/analysis_report.md", "w", encoding="utf-8") as f:
    f.write(report)
print("[OK] output/analysis_report.md saved")

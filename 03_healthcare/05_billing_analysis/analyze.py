# -*- coding: utf-8 -*-
import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CSV_PATH = os.path.join(OUTPUT_DIR, "cleaned_claims_202401.csv")

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
df["claim_date"] = pd.to_datetime(df["claim_date"], format="%Y-%m-%d", errors="coerce")

# --- Dept summary ---
dept_grp = df.groupby("dept").agg(
    total_claim_amount=("claim_amount", "sum"),
    total_net_amount=("net_amount", "sum"),
    avg_reduction_rate=("reduction_rate", "mean"),
    total_patients=("patient_count", "sum"),
    row_count=("claim_id", "count"),
).reset_index()

dept_grp["collection_rate"] = df.groupby("dept").apply(
    lambda g: (g["payment_status"] == "支払済み").mean()
).values

dept_summary_path = os.path.join(OUTPUT_DIR, "dept_summary_202401.csv")
dept_grp.to_csv(dept_summary_path, index=False, encoding="utf-8-sig")
print("[OK] Dept summary saved: {}".format(dept_summary_path))

# --- Insurance summary ---
ins_grp = df.groupby("insurance_type").agg(
    row_count=("claim_id", "count"),
    avg_points=("total_points", "mean"),
    total_claim_amount=("claim_amount", "sum"),
).reset_index()

# --- Daily trend ---
daily = df.groupby(df["claim_date"].dt.date).agg(
    daily_net_amount=("net_amount", "sum"),
    daily_claim_amount=("claim_amount", "sum"),
).reset_index()
daily.columns = ["date", "daily_net_amount", "daily_claim_amount"]

# --- Report ---
report_lines = []
report_lines.append("# C-51 Billing Analysis Report 2024-01")
report_lines.append("")
report_lines.append("## 1. Overview")
report_lines.append("")
report_lines.append("- Total records: {}".format(len(df)))
report_lines.append("- Total claim amount: {:,.0f} yen".format(df["claim_amount"].sum()))
report_lines.append("- Total net amount: {:,.0f} yen".format(df["net_amount"].sum()))
report_lines.append("- Average reduction rate: {:.2%}".format(df["reduction_rate"].mean()))
report_lines.append("- Returned claims: {} ({:.1%})".format(
    (df["is_returned"] == 1).sum(),
    (df["is_returned"] == 1).mean()
))
report_lines.append("")
report_lines.append("## 2. By Department")
report_lines.append("")
report_lines.append("| Dept | ClaimAmount | NetAmount | AvgReductionRate | CollectionRate |")
report_lines.append("|------|-------------|-----------|-----------------|----------------|")
for _, row in dept_grp.iterrows():
    report_lines.append("| {} | {:,.0f} | {:,.0f} | {:.2%} | {:.2%} |".format(
        row["dept"], row["total_claim_amount"], row["total_net_amount"],
        row["avg_reduction_rate"], row["collection_rate"]
    ))
report_lines.append("")
report_lines.append("## 3. By Insurance Type")
report_lines.append("")
report_lines.append("| InsuranceType | Count | AvgPoints | TotalClaimAmount |")
report_lines.append("|--------------|-------|-----------|-----------------|")
for _, row in ins_grp.iterrows():
    report_lines.append("| {} | {} | {:,.1f} | {:,.0f} |".format(
        row["insurance_type"], int(row["row_count"]),
        row["avg_points"], row["total_claim_amount"]
    ))
report_lines.append("")
report_lines.append("## 4. Daily Revenue Trend (Top 5 Days)")
report_lines.append("")
top5 = daily.nlargest(5, "daily_net_amount")
report_lines.append("| Date | NetAmount | ClaimAmount |")
report_lines.append("|------|-----------|-------------|")
for _, row in top5.iterrows():
    report_lines.append("| {} | {:,.0f} | {:,.0f} |".format(
        row["date"], row["daily_net_amount"], row["daily_claim_amount"]
    ))
report_lines.append("")

report_path = os.path.join(OUTPUT_DIR, "analysis_report.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))
print("[OK] Report saved: {}".format(report_path))

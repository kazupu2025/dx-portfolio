# -*- coding: utf-8 -*-
import os
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CSV_PATH = os.path.join(OUTPUT_DIR, "cleaned_visits_202401.csv")

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
df["asking_price"] = pd.to_numeric(df["asking_price"], errors="coerce")
df["days_to_contract"] = pd.to_numeric(df["days_to_contract"], errors="coerce")
df["is_contracted"] = pd.to_numeric(df["is_contracted"], errors="coerce")

# 1. Property type analysis
type_group = df.groupby("property_type").agg(
    visit_count=("visit_id", "count"),
    contract_count=("is_contracted", "sum"),
    avg_days_to_contract=("days_to_contract", "mean"),
    avg_asking_price=("asking_price", "mean"),
).reset_index()
type_group["conversion_rate"] = type_group["contract_count"] / type_group["visit_count"]
type_group = type_group.round(2)

# 2. Area analysis
area_group = df.groupby("area").agg(
    visit_count=("visit_id", "count"),
    contract_count=("is_contracted", "sum"),
).reset_index()
area_group["conversion_rate"] = (area_group["contract_count"] / area_group["visit_count"]).round(4)

# 3. Staff analysis
staff_group = df.groupby("staff_id").agg(
    visit_count=("visit_id", "count"),
    contract_count=("is_contracted", "sum"),
).reset_index()
staff_group["conversion_rate"] = (staff_group["contract_count"] / staff_group["visit_count"]).round(4)

# Output summary CSV
summary = type_group.rename(columns={
    "property_type": "物件タイプ",
    "visit_count": "内見件数",
    "contract_count": "成約件数",
    "avg_days_to_contract": "平均成約日数",
    "avg_asking_price": "平均物件価格(万円)",
    "conversion_rate": "成約率",
})
out_csv = os.path.join(OUTPUT_DIR, "property_summary_202401.csv")
summary.to_csv(out_csv, index=False, encoding="utf-8-sig")
print("[OK] Summary CSV saved: {}".format(out_csv))

# Output markdown report
report_path = os.path.join(OUTPUT_DIR, "analysis_report.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("# 物件内見予約・成約率分析レポート\n\n")
    f.write("## 1. 物件タイプ別成約率・平均成約日数・平均価格\n\n")
    f.write(type_group.to_markdown(index=False))
    f.write("\n\n")
    f.write("## 2. エリア別内見件数・成約率\n\n")
    f.write(area_group.to_markdown(index=False))
    f.write("\n\n")
    f.write("## 3. スタッフ別担当件数・成約率\n\n")
    f.write(staff_group.to_markdown(index=False))
    f.write("\n")
print("[OK] Report saved: {}".format(report_path))

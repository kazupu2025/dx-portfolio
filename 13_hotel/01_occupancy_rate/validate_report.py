# -*- coding: utf-8 -*-
import os
import sys
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

REPORT_PATH = os.path.join(OUTPUT_DIR, "analysis_report.md")
ROOM_CSV_PATH = os.path.join(OUTPUT_DIR, "room_summary_202401.csv")

results = []


def check(name, passed, detail=""):
    status = "[PASS]" if passed else "[FAIL]"
    msg = "{} {}".format(status, name)
    if detail:
        msg += " | " + detail
    print(msg)
    results.append(passed)


# Check 1: report file exists
check("analysis_report.md exists", os.path.exists(REPORT_PATH))

# Check 2: room summary exists
check("room_summary_202401.csv exists", os.path.exists(ROOM_CSV_PATH))

if not os.path.exists(ROOM_CSV_PATH):
    print("Result: {}/10 checks passed".format(sum(results)))
    sys.exit(1)

df = pd.read_csv(ROOM_CSV_PATH, encoding="utf-8-sig")

check("room_summary has 4 rows (one per room type)", len(df) == 4, "rows={}".format(len(df)))
check("room_type column present", "room_type" in df.columns)
check("total_revenue column present and > 0", "total_revenue" in df.columns and (df["total_revenue"] > 0).any())
check("occupancy_rate between 0 and 1",
      "occupancy_rate" in df.columns and df["occupancy_rate"].between(0, 1).all(),
      "min={}, max={}".format(
          df["occupancy_rate"].min() if "occupancy_rate" in df.columns else "N/A",
          df["occupancy_rate"].max() if "occupancy_rate" in df.columns else "N/A"))
check("cancel_rate between 0 and 1",
      "cancel_rate" in df.columns and df["cancel_rate"].between(0, 1).all())
check("loss_revenue >= 0",
      "loss_revenue" in df.columns and (df["loss_revenue"] >= 0).all())

# Check report content
if os.path.exists(REPORT_PATH):
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    check("Report contains summary section", "総合サマリー" in content)
    check("Report contains room type section", "客室タイプ別分析" in content)
else:
    check("Report contains summary section", False)
    check("Report contains room type section", False)

passed = sum(results)
total = len(results)
print("Result: {}/{} checks passed".format(passed, total))
if passed < total:
    sys.exit(1)

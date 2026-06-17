# -*- coding: utf-8 -*-
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

REPORT_PATH = os.path.join(OUTPUT_DIR, "analysis_report.md")
WORKER_CSV = os.path.join(OUTPUT_DIR, "worker_summary_202401.csv")

results = []


def check(label, condition):
    status = "[PASS]" if condition else "[FAIL]"
    results.append((status, label))
    print(f"{status} {label}")


# 1. analysis_report.md exists
check("analysis_report.md が存在する", os.path.exists(REPORT_PATH))

# 2. worker_summary_202401.csv exists
check("worker_summary_202401.csv が存在する", os.path.exists(WORKER_CSV))

if os.path.exists(REPORT_PATH):
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        report_text = f.read()
else:
    report_text = ""

# 3. Report contains worker section
check("レポートにWorker KPI Summaryセクションが含まれる", "Worker KPI Summary" in report_text)

# 4. Report contains zone analysis
check("レポートにZone Analysisセクションが含まれる", "Zone Analysis" in report_text)

# 5. Report contains task type analysis
check("レポートにTask Type Analysisセクションが含まれる", "Task Type Analysis" in report_text)

# 6. Report contains KPI distribution
check("レポートにKPI Flag Distributionセクションが含まれる", "KPI Flag Distribution" in report_text)

if os.path.exists(WORKER_CSV):
    ws = pd.read_csv(WORKER_CSV, encoding="utf-8-sig")
else:
    ws = pd.DataFrame()

# 7. Worker summary has >= 15 workers
check("worker_summary に >= 15 名含まれる", len(ws) >= 15)

# 8. Worker summary has required columns
required_ws_cols = ["worker_id", "avg_throughput", "avg_error_rate", "kpi_flag"]
check("worker_summary の必須列が存在する", all(c in ws.columns for c in required_ws_cols))

# 9. avg_throughput > 0 for all workers
if "avg_throughput" in ws.columns:
    check("avg_throughput > 0", (ws["avg_throughput"] > 0).all())
else:
    check("avg_throughput > 0", False)

# 10. kpi_flag values are valid
if "kpi_flag" in ws.columns:
    valid_flags = {"優秀", "標準"}
    actual_flags = set(ws["kpi_flag"].dropna().unique())
    check("kpi_flag の値が 優秀/標準 のみ", actual_flags.issubset(valid_flags))
else:
    check("kpi_flag の値が 優秀/標準 のみ", False)

passed = sum(1 for s, _ in results if s == "[PASS]")
total = len(results)
print(f"\nResult: {passed}/{total} checks passed")

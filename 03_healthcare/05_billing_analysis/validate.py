# -*- coding: utf-8 -*-
import os
import pandas as pd
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CSV_PATH = os.path.join(OUTPUT_DIR, "cleaned_claims_202401.csv")

checks = []


def check(label, condition):
    status = "[PASS]" if condition else "[FAIL]"
    checks.append((label, status))
    print("{} {}".format(status, label))


# 1. File exists
check("File exists", os.path.exists(CSV_PATH))

if not os.path.exists(CSV_PATH):
    print("Result: 1/18 checks passed")
    sys.exit(1)

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# 2. Row count >= 420
check("Row count >= 420", len(df) >= 420)

# 3. Required columns present
REQUIRED_COLS = [
    "claim_date", "claim_id", "dept", "insurance_type",
    "patient_count", "total_points", "claim_amount", "reduction_amount",
    "payment_status", "net_amount", "reduction_rate",
    "is_returned", "collection_flag", "source_file"
]
check("Required columns present", all(c in df.columns for c in REQUIRED_COLS))

# 4. claim_date format YYYY-MM-DD
date_ok = df["claim_date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$").all()
check("claim_date format YYYY-MM-DD", date_ok)

# 5. claim_id unique
check("claim_id unique", df["claim_id"].nunique() == len(df))

# 6. dept has 5 kinds
check("dept has 5 kinds", df["dept"].nunique() == 5)

# 7. insurance_type has 3 kinds
check("insurance_type has 3 kinds", df["insurance_type"].nunique() == 3)

# 8. patient_count >= 1
check("patient_count >= 1", (df["patient_count"] >= 1).all())

# 9. total_points > 0
check("total_points > 0", (df["total_points"] > 0).all())

# 10. claim_amount > 0
check("claim_amount > 0", (df["claim_amount"] > 0).all())

# 11. reduction_amount >= 0
check("reduction_amount >= 0", (df["reduction_amount"] >= 0).all())

# 12. net_amount >= 0 (reduction_amount does not exceed claim_amount)
check("net_amount >= 0", (df["net_amount"] >= 0).all())

# 13. reduction_rate in [0, 1]
check("reduction_rate in [0,1]", ((df["reduction_rate"] >= 0) & (df["reduction_rate"] <= 1)).all())

# 14. is_returned values 0 or 1 only
check("is_returned values 0 or 1 only", df["is_returned"].isin([0, 1]).all())

# 15. collection_flag has exactly 2 kinds
check("collection_flag has 2 kinds", df["collection_flag"].nunique() == 2)

# 16. missing rate <= 15%
total_cells = df.shape[0] * df.shape[1]
missing_rate = df.isnull().sum().sum() / total_cells
check("missing rate <= 15%", missing_rate <= 0.15)

# 17. source_file has 3 kinds
check("source_file has 3 kinds", df["source_file"].nunique() == 3)

# 18. returned count >= 1
check("returned count >= 1", (df["is_returned"] == 1).sum() >= 1)

passed = sum(1 for _, s in checks if s == "[PASS]")
total = len(checks)
print("")
print("Result: {}/{} checks passed".format(passed, total))

if passed < total:
    sys.exit(1)

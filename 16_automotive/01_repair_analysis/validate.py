# -*- coding: utf-8 -*-
import os
import re
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CSV_PATH = os.path.join(OUTPUT_DIR, "cleaned_orders_202401.csv")

results = []

def check(label, condition):
    status = "[PASS]" if condition else "[FAIL]"
    results.append((status, label))
    print(f"{status} {label}")

def main():
    # 1. File exists
    check("File exists: cleaned_orders_202401.csv", os.path.exists(CSV_PATH))
    if not os.path.exists(CSV_PATH):
        print("Result: 1/18 checks passed")
        return

    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

    # 2. Row count >= 420
    check("Row count >= 420", len(df) >= 420)

    # 3. Required columns present
    required = [
        "order_date", "order_id", "shop_name", "work_type", "tech_id",
        "estimated_days", "actual_days", "labor_cost", "parts_cost", "status",
        "total_cost", "delay_days", "is_delayed", "is_returned", "efficiency_flag", "source_file"
    ]
    check("Required columns present", all(c in df.columns for c in required))

    # 4. order_date format YYYY-MM-DD
    date_ok = df["order_date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$").all()
    check("order_date format YYYY-MM-DD", bool(date_ok))

    # 5. order_id uniqueness
    check("order_id is unique", df["order_id"].nunique() == len(df))

    # 6. shop_name has 3 kinds
    check("shop_name has 3 kinds", df["shop_name"].nunique() == 3)

    # 7. work_type has 4 kinds
    check("work_type has 4 kinds", df["work_type"].nunique() == 4)

    # 8. estimated_days >= 1
    check("estimated_days >= 1", (df["estimated_days"] >= 1).all())

    # 9. actual_days >= 1
    check("actual_days >= 1", (df["actual_days"] >= 1).all())

    # 10. labor_cost >= 0
    check("labor_cost >= 0", (df["labor_cost"] >= 0).all())

    # 11. parts_cost >= 0
    check("parts_cost >= 0", (df["parts_cost"] >= 0).all())

    # 12. total_cost >= 0
    check("total_cost >= 0", (df["total_cost"] >= 0).all())

    # 13. is_delayed only 0 or 1
    check("is_delayed only 0/1", set(df["is_delayed"].unique()).issubset({0, 1}))

    # 14. is_returned only 0 or 1
    check("is_returned only 0/1", set(df["is_returned"].unique()).issubset({0, 1}))

    # 15. efficiency_flag has exactly 2 kinds
    check("efficiency_flag has 2 kinds", df["efficiency_flag"].nunique() == 2)

    # 16. Missing rate <= 15%
    total_cells = df.shape[0] * df.shape[1]
    missing_rate = df.isnull().sum().sum() / total_cells
    check("Missing rate <= 15%", missing_rate <= 0.15)

    # 17. source_file has 3 kinds
    check("source_file has 3 kinds", df["source_file"].nunique() == 3)

    # 18. Returned count >= 1
    check("Re-entry (再入庫) count >= 1", (df["status"] == "再入庫").sum() >= 1)

    passed = sum(1 for s, _ in results if s == "[PASS]")
    total = len(results)
    print(f"\nResult: {passed}/{total} checks passed")

if __name__ == "__main__":
    main()

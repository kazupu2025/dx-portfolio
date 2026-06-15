"""
B-14 バリデーション (18チェック)
"""
import pandas as pd
import yaml
import sys
import subprocess
from pathlib import Path

BASE = Path(__file__).parent.parent
OUT = Path(__file__).parent
CSV = OUT / "cleaned_rental_202401.csv"
LOG = OUT / "cleanse.log"

KEEP_COLS = {
    "property_id", "property_name", "area", "property_type",
    "rent", "management_fee", "occupancy_status",
    "move_in_date", "move_out_date",
    "management_cost", "repair_cost",
    "is_vacant", "monthly_revenue", "total_cost", "net_income",
    "source_file",
}

def load_cfg():
    with open(BASE / "config.yml", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_checks(df, cfg):
    results = {}

    # 1. csv_exists
    results["csv_exists"] = CSV.exists()
    # 2. log_exists
    results["log_exists"] = LOG.exists()
    # 3. schema
    cols = set(df.columns)
    results["schema"] = (KEEP_COLS == cols)
    # 4-8. null checks
    results["property_id_nan"] = df["property_id"].notna().all()
    results["area_nan"] = df["area"].notna().all()
    results["property_type_nan"] = df["property_type"].notna().all()
    results["rent_nan"] = df["rent"].notna().all()
    results["occupancy_status_nan"] = df["occupancy_status"].notna().all()
    results["is_vacant_nan"] = df["is_vacant"].notna().all()
    # 10-14. non-negative
    results["rent_nonneg"] = (pd.to_numeric(df["rent"], errors="coerce").fillna(0) >= 0).all()
    results["management_fee_nonneg"] = (pd.to_numeric(df["management_fee"], errors="coerce").fillna(0) >= 0).all()
    results["management_cost_nonneg"] = (pd.to_numeric(df["management_cost"], errors="coerce").fillna(0) >= 0).all()
    results["repair_cost_nonneg"] = (pd.to_numeric(df["repair_cost"], errors="coerce").fillna(0) >= 0).all()
    results["monthly_revenue_nonneg"] = (pd.to_numeric(df["monthly_revenue"], errors="coerce").fillna(0) >= 0).all()
    # 15. status values
    valid_statuses = {"入居中", "空室", "募集中"}
    results["status_values"] = set(df["occupancy_status"].dropna().unique()).issubset(valid_statuses)
    # 16. area_count
    results["area_count"] = df["area"].nunique() == cfg["expected_area_count"]
    # 17. property_type_count
    results["property_type_count"] = df["property_type"].nunique() == cfg["expected_property_type_count"]
    # 18. row_count
    results["row_count"] = cfg["min_rows"] <= len(df) <= cfg["max_rows"]

    return results

def main():
    cfg = load_cfg()
    max_rounds = 5

    for round_n in range(1, max_rounds + 1):
        print(f"\n--- PDCA Round {round_n} ---")

        if not CSV.exists():
            print("CSV not found, running cleanse.py...")
            subprocess.run(["C:/Users/realp/miniconda3/python.exe", str(OUT / "cleanse.py")], check=True)

        df = pd.read_csv(CSV, encoding="utf-8-sig")
        results = run_checks(df, cfg)

        passed = sum(1 for v in results.values() if v)
        total = len(results)
        print(f"Results: {passed}/{total} PASS")

        for name, ok in results.items():
            status = "PASS" if ok else "FAIL"
            print(f"  [{status}] {name}")

        if passed == total:
            print(f"\nAll {total} checks PASSED in round {round_n}!")
            return 0

        # Re-run cleanse if not all passed
        if round_n < max_rounds:
            print("\nRe-running cleanse.py...")
            subprocess.run(["C:/Users/realp/miniconda3/python.exe", str(OUT / "cleanse.py")], check=True)

    print(f"\nWARNING: Not all checks passed after {max_rounds} rounds")
    return 1

if __name__ == "__main__":
    sys.exit(main())

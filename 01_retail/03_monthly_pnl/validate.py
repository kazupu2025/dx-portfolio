"""
C-19: validate.py
cleaned_pnl_202401.csv の品質を 18 項目チェックする
em-dash や絵文字は使用しない（Windows CP932 対応）
"""
import os
import sys
import re
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "output", "cleaned_pnl_202401.csv")

REQUIRED_COLS = [
    "store_id", "store_name", "year_month",
    "planned_revenue", "actual_revenue",
    "planned_cogs", "actual_cogs",
    "planned_labor", "actual_labor",
    "planned_other", "actual_other",
    "planned_gross_profit", "actual_gross_profit",
    "planned_operating_profit", "actual_operating_profit",
    "revenue_variance", "revenue_variance_ratio",
    "profit_variance", "profit_variance_ratio",
    "profit_flag", "source_file",
]

results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    return condition


def run_checks(df):
    # 1. 行数 400 以上
    check("行数400以上", len(df) >= 400, f"actual={len(df)}")

    # 2. 必須列すべて存在
    missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
    check("必須列存在", len(missing_cols) == 0, f"missing={missing_cols}")

    # 3. year_month 形式（YYYY-MM または YYYY-WNN）
    if "year_month" in df.columns:
        pattern = re.compile(r"^\d{4}-(\d{2}|W\d{2})$")
        bad = df[~df["year_month"].astype(str).str.match(r"^\d{4}-(\d{2}|W\d{2})$")]
        check("year_month形式正常", len(bad) == 0, f"bad_count={len(bad)}")
    else:
        check("year_month形式正常", False, "column missing")

    # 4. store_id 種類 5 以上
    if "store_id" in df.columns:
        n = df["store_id"].nunique()
        check("store_id種類5以上", n >= 5, f"unique={n}")
    else:
        check("store_id種類5以上", False, "column missing")

    # 5. planned_revenue > 0
    if "planned_revenue" in df.columns:
        bad = (df["planned_revenue"] <= 0).sum()
        check("planned_revenue>0", bad == 0, f"violations={bad}")
    else:
        check("planned_revenue>0", False, "column missing")

    # 6. actual_revenue > 0
    if "actual_revenue" in df.columns:
        bad = (df["actual_revenue"] <= 0).sum()
        check("actual_revenue>0", bad == 0, f"violations={bad}")
    else:
        check("actual_revenue>0", False, "column missing")

    # 7. actual_cogs >= 0
    if "actual_cogs" in df.columns:
        bad = (df["actual_cogs"] < 0).sum()
        check("actual_cogs>=0", bad == 0, f"violations={bad}")
    else:
        check("actual_cogs>=0", False, "column missing")

    # 8. actual_labor >= 0
    if "actual_labor" in df.columns:
        bad = (df["actual_labor"] < 0).sum()
        check("actual_labor>=0", bad == 0, f"violations={bad}")
    else:
        check("actual_labor>=0", False, "column missing")

    # 9. actual_gross_profit 整合性（actual_revenue - actual_cogs）
    if all(c in df.columns for c in ["actual_gross_profit", "actual_revenue", "actual_cogs"]):
        diff = (df["actual_gross_profit"] - (df["actual_revenue"] - df["actual_cogs"])).abs()
        bad = (diff > 1).sum()
        check("actual_gross_profit整合性", bad == 0, f"violations={bad}")
    else:
        check("actual_gross_profit整合性", False, "column missing")

    # 10. actual_operating_profit 整合性
    if all(c in df.columns for c in ["actual_operating_profit", "actual_gross_profit", "actual_labor", "actual_other"]):
        diff = (df["actual_operating_profit"] - (df["actual_gross_profit"] - df["actual_labor"] - df["actual_other"])).abs()
        bad = (diff > 1).sum()
        check("actual_operating_profit整合性", bad == 0, f"violations={bad}")
    else:
        check("actual_operating_profit整合性", False, "column missing")

    # 11. revenue_variance_ratio 範囲（-1〜1）
    if "revenue_variance_ratio" in df.columns:
        non_nan = df["revenue_variance_ratio"].dropna()
        bad = ((non_nan < -1) | (non_nan > 1)).sum()
        check("revenue_variance_ratio範囲-1to1", bad == 0, f"violations={bad}")
    else:
        check("revenue_variance_ratio範囲-1to1", False, "column missing")

    # 12. profit_flag 値域（赤字/未達/達成）
    if "profit_flag" in df.columns:
        valid_flags = {"赤字", "未達", "達成"}
        bad = (~df["profit_flag"].isin(valid_flags)).sum()
        check("profit_flag値域", bad == 0, f"violations={bad}")
    else:
        check("profit_flag値域", False, "column missing")

    # 13. source_file 列存在
    check("source_file列存在", "source_file" in df.columns)

    # 14. 欠損率 15% 以下（数値列合計）
    numeric_cols = ["planned_revenue", "actual_revenue", "planned_cogs", "actual_cogs",
                    "planned_labor", "actual_labor", "planned_other", "actual_other"]
    if all(c in df.columns for c in numeric_cols):
        total_cells = len(df) * len(numeric_cols)
        missing_cells = df[numeric_cols].isna().sum().sum()
        rate = missing_cells / total_cells if total_cells > 0 else 0
        check("欠損率15%以下", rate <= 0.15, f"rate={rate:.3f}")
    else:
        check("欠損率15%以下", False, "column missing")

    # 15. planned_gross_profit 整合性
    if all(c in df.columns for c in ["planned_gross_profit", "planned_revenue", "planned_cogs"]):
        diff = (df["planned_gross_profit"] - (df["planned_revenue"] - df["planned_cogs"])).abs()
        bad = (diff > 1).sum()
        check("planned_gross_profit整合性", bad == 0, f"violations={bad}")
    else:
        check("planned_gross_profit整合性", False, "column missing")

    # 16. planned_operating_profit 整合性
    if all(c in df.columns for c in ["planned_operating_profit", "planned_gross_profit", "planned_labor", "planned_other"]):
        diff = (df["planned_operating_profit"] - (df["planned_gross_profit"] - df["planned_labor"] - df["planned_other"])).abs()
        bad = (diff > 1).sum()
        check("planned_operating_profit整合性", bad == 0, f"violations={bad}")
    else:
        check("planned_operating_profit整合性", False, "column missing")

    # 17. revenue_variance 整合性
    if all(c in df.columns for c in ["revenue_variance", "actual_revenue", "planned_revenue"]):
        diff = (df["revenue_variance"] - (df["actual_revenue"] - df["planned_revenue"])).abs()
        bad = (diff > 1).sum()
        check("revenue_variance整合性", bad == 0, f"violations={bad}")
    else:
        check("revenue_variance整合性", False, "column missing")

    # 18. profit_variance 整合性
    if all(c in df.columns for c in ["profit_variance", "actual_operating_profit", "planned_operating_profit"]):
        diff = (df["profit_variance"] - (df["actual_operating_profit"] - df["planned_operating_profit"])).abs()
        bad = (diff > 1).sum()
        check("profit_variance整合性", bad == 0, f"violations={bad}")
    else:
        check("profit_variance整合性", False, "column missing")


def main():
    print("[validate.py] Checking: " + OUTPUT_FILE)

    # 0. ファイル存在チェック
    if not check("CSVファイル存在", os.path.isfile(OUTPUT_FILE)):
        print("\n[RESULT] FAIL - file not found")
        sys.exit(1)

    df = pd.read_csv(OUTPUT_FILE, encoding="utf-8-sig")
    run_checks(df)

    print(f"\n{'No':>3}  {'Check':<40}  {'Status':<6}  Detail")
    print("-" * 80)
    for i, (name, status, detail) in enumerate(results, 1):
        print(f"{i:>3}  {name:<40}  {status:<6}  {detail}")

    total = len(results)
    passed = sum(1 for _, s, _ in results if s == "PASS")
    failed = total - passed

    print(f"\n[RESULT] {passed}/{total} PASS, {failed} FAIL")
    if failed > 0:
        sys.exit(1)
    else:
        print("[validate.py] All checks passed.")


if __name__ == "__main__":
    main()

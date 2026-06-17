# -*- coding: utf-8 -*-
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "output", "cleaned_contracts_202401.csv")

REQUIRED_COLS = [
    "contract_date", "contract_id", "plan", "industry",
    "monthly_fee", "usage_months", "login_count", "support_count",
    "status", "churn_reason", "ltv", "is_churned",
    "churn_risk", "arpu_grade", "source_file"
]

results = []


def check(label, passed):
    mark = "[PASS]" if passed else "[FAIL]"
    print(f"{mark} {label}")
    results.append(passed)


def main():
    # Check 1: File exists
    check("ファイル存在確認", os.path.exists(OUTPUT_FILE))
    if not os.path.exists(OUTPUT_FILE):
        print(f"Result: 1/18 checks passed")
        return

    df = pd.read_csv(OUTPUT_FILE, encoding="utf-8-sig")

    # Check 2: Row count >= 420
    check(f"行数>=420 (実際: {len(df)})", len(df) >= 420)

    # Check 3: Required columns present
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    check(f"必須列の存在 (不足: {missing})", len(missing) == 0)

    # Check 4: contract_date format YYYY-MM-DD
    date_ok = df["contract_date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$").all()
    check("contract_dateフォーマット (YYYY-MM-DD)", bool(date_ok))

    # Check 5: contract_id uniqueness per source file
    # IDs are repeated across 3 styles but should be unique within each style
    dup_within = df.groupby("source_file")["contract_id"].apply(lambda x: x.duplicated().any())
    check("contract_id一意性 (各sourceファイル内)", not dup_within.any())

    # Check 6: plan has 3 kinds
    plans = df["plan"].dropna().unique()
    check(f"plan種類==3 (実際: {sorted(plans)})", len(plans) == 3)

    # Check 7: industry has 5 kinds
    industries = df["industry"].dropna().unique()
    check(f"industry種類==5 (実際: {sorted(industries)})", len(industries) == 5)

    # Check 8: monthly_fee > 0
    check("monthly_fee>0", (pd.to_numeric(df["monthly_fee"], errors="coerce") > 0).all())

    # Check 9: usage_months >= 1
    check("usage_months>=1", (pd.to_numeric(df["usage_months"], errors="coerce") >= 1).all())

    # Check 10: login_count >= 0
    check("login_count>=0", (pd.to_numeric(df["login_count"], errors="coerce") >= 0).all())

    # Check 11: support_count >= 0
    check("support_count>=0", (pd.to_numeric(df["support_count"], errors="coerce") >= 0).all())

    # Check 12: ltv > 0
    check("ltv>0", (pd.to_numeric(df["ltv"], errors="coerce") > 0).all())

    # Check 13: is_churned only 0 or 1
    is_churned_vals = df["is_churned"].dropna().unique()
    check(f"is_churned 0/1のみ (実際: {sorted(is_churned_vals)})",
          set(is_churned_vals).issubset({0, 1}))

    # Check 14: churn_risk has 3 kinds
    risk_vals = df["churn_risk"].dropna().unique()
    check(f"churn_risk種類==3 (実際: {sorted(risk_vals)})", len(risk_vals) == 3)

    # Check 15: arpu_grade has 2 kinds
    arpu_vals = df["arpu_grade"].dropna().unique()
    check(f"arpu_grade種類==2 (実際: {sorted(arpu_vals)})", len(arpu_vals) == 2)

    # Check 16: Missing rate <= 15% (churn_reason除く)
    check_cols = [c for c in REQUIRED_COLS if c != "churn_reason"]
    missing_rate = df[check_cols].isnull().mean().max()
    check(f"欠損率<=15% (churn_reason除く、最大: {missing_rate:.1%})", missing_rate <= 0.15)

    # Check 17: source_file has 3 kinds
    src_vals = df["source_file"].dropna().unique()
    check(f"source_file種類==3 (実際: {sorted(src_vals)})", len(src_vals) == 3)

    # Check 18: churn count >= 1
    churn_count = int(df["is_churned"].sum())
    check(f"解約件数>=1 (実際: {churn_count})", churn_count >= 1)

    passed = sum(results)
    total = len(results)
    print(f"Result: {passed}/{total} checks passed")


if __name__ == "__main__":
    main()

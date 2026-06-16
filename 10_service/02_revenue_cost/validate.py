"""
C-21: データバリデーション (18項目)
全PASS必須。Windows CP932エラー回避のためASCII文字のみ使用。
"""
import sys
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).parent
CSV_PATH = BASE / "output" / "cleaned_revenue_cost_202401.csv"

REQUIRED_COLS = [
    "project_id", "client_name", "service_type", "department",
    "contract_month", "revenue", "direct_cost", "allocated_overhead",
    "hours_spent", "is_completed", "source_file",
    "total_cost", "gross_profit", "operating_profit",
    "gross_margin_ratio", "operating_margin_ratio", "revenue_per_hour",
    "profit_flag",
]

VALID_SERVICE_TYPES = {"SaaS利用料", "受託開発", "保守サポート", "コンサルティング", "研修・教育"}
VALID_PROFIT_FLAGS = {"赤字", "低収益", "良好"}

results = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    msg = f"[{status}] {name}"
    if detail:
        msg += f" : {detail}"
    results.append((name, cond, detail))
    print(msg)


def main():
    print("=== validate.py (18 checks) ===\n")

    # [1] CSV存在確認
    check("01_csv_exists", CSV_PATH.exists(), str(CSV_PATH))

    if not CSV_PATH.exists():
        print("\nCSVが存在しないため残りのチェックをスキップします")
        sys.exit(1)

    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

    # [2] 行数400以上
    check("02_row_count_ge_400", len(df) >= 400, f"rows={len(df)}")

    # [3] 必須列存在
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    check("03_required_columns", len(missing) == 0, f"missing={missing}")

    # [4] contract_month形式 (YYYY-MM)
    import re
    pattern = re.compile(r"^\d{4}-\d{2}$")
    invalid_months = df["contract_month"].dropna().apply(lambda x: not bool(pattern.match(str(x))))
    check("04_contract_month_format", not invalid_months.any(), f"invalid={invalid_months.sum()}")

    # [5] project_idユニーク性
    dup_count = df["project_id"].duplicated().sum()
    check("05_project_id_unique", dup_count == 0, f"duplicates={dup_count}")

    # [6] revenue > 0
    invalid_rev = (df["revenue"] <= 0).sum()
    check("06_revenue_positive", invalid_rev == 0, f"invalid={invalid_rev}")

    # [7] direct_cost >= 0
    invalid_dc = (df["direct_cost"] < 0).sum()
    check("07_direct_cost_nonneg", invalid_dc == 0, f"invalid={invalid_dc}")

    # [8] allocated_overhead >= 0
    invalid_oh = (df["allocated_overhead"] < 0).sum()
    check("08_allocated_overhead_nonneg", invalid_oh == 0, f"invalid={invalid_oh}")

    # [9] gross_profit整合性 (revenue - direct_cost)
    expected_gp = (df["revenue"] - df["direct_cost"]).round(2)
    actual_gp = df["gross_profit"].round(2)
    gp_mismatch = (expected_gp - actual_gp).abs() > 1
    check("09_gross_profit_consistency", not gp_mismatch.any(), f"mismatch={gp_mismatch.sum()}")

    # [10] operating_profit整合性 (revenue - total_cost)
    expected_op = (df["revenue"] - df["total_cost"]).round(2)
    actual_op = df["operating_profit"].round(2)
    op_mismatch = (expected_op - actual_op).abs() > 1
    check("10_operating_profit_consistency", not op_mismatch.any(), f"mismatch={op_mismatch.sum()}")

    # [11] gross_margin_ratio範囲 (-1 ~ 1)
    valid_range = df["gross_margin_ratio"].dropna()
    out_of_range = ((valid_range < -1) | (valid_range > 1)).sum()
    check("11_gross_margin_ratio_range", out_of_range == 0, f"out_of_range={out_of_range}")

    # [12] profit_flag値域
    invalid_flags = (~df["profit_flag"].isin(VALID_PROFIT_FLAGS)).sum()
    check("12_profit_flag_values", invalid_flags == 0, f"invalid={invalid_flags}")

    # [13] service_type種類 (5種類すべて存在)
    found_services = set(df["service_type"].dropna().unique())
    missing_sv = VALID_SERVICE_TYPES - found_services
    check("13_service_type_5kinds", len(missing_sv) == 0, f"missing={missing_sv}")

    # [14] department種類 (3以上)
    dept_count = df["department"].nunique()
    check("14_department_ge_3kinds", dept_count >= 3, f"dept_count={dept_count}")

    # [15] is_completedがbool (True/False)
    invalid_bool = (~df["is_completed"].isin([True, False])).sum()
    check("15_is_completed_bool", invalid_bool == 0, f"invalid={invalid_bool}")

    # [16] source_file列存在・非空
    sf_null = df["source_file"].isna().sum()
    check("16_source_file_notnull", sf_null == 0, f"nulls={sf_null}")

    # [17] 欠損率15%以下（数値列全体）
    num_cols = ["revenue", "direct_cost", "allocated_overhead", "hours_spent"]
    max_null_ratio = df[num_cols].isna().mean().max()
    check("17_null_rate_le_15pct", max_null_ratio <= 0.15, f"max_null_ratio={max_null_ratio:.3f}")

    # [18] total_cost整合性 (direct_cost + allocated_overhead)
    expected_tc = (df["direct_cost"] + df["allocated_overhead"]).round(2)
    actual_tc = df["total_cost"].round(2)
    tc_mismatch = (expected_tc - actual_tc).abs() > 1
    check("18_total_cost_consistency", not tc_mismatch.any(), f"mismatch={tc_mismatch.sum()}")

    # 結果サマリー
    print(f"\n=== 結果サマリー ===")
    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    print(f"PASS: {passed} / {len(results)}")
    print(f"FAIL: {failed} / {len(results)}")

    if failed > 0:
        print("\n--- FAIL一覧 ---")
        for name, ok, detail in results:
            if not ok:
                print(f"  FAIL {name} : {detail}")
        sys.exit(1)
    else:
        print("\n全チェックPASS")
        sys.exit(0)


if __name__ == "__main__":
    main()

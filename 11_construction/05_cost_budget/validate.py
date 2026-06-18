# -*- coding: utf-8 -*-
"""
C-58: validate.py -- クレンジング結果の品質チェック (18項目)
全PASS必須。絵文字・em-dashは使用しない(Windows CP932互換)。
"""

import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "output" / "cleaned_costs_202401.csv"

REQUIRED_COLS = [
    "record_date", "record_id", "project_no", "work_type", "cost_category",
    "budget_amount", "actual_amount", "is_over_budget",
    "variance", "variance_rate", "budget_status", "variance_grade", "source_file",
]

EXPECTED_WORK_TYPES = {"土工", "コンクリート工", "鉄筋工", "仮設工"}
EXPECTED_COST_CATEGORIES = {"材料費", "労務費", "外注費"}
EXPECTED_BUDGET_STATUSES = {"超過", "予算内"}
EXPECTED_VARIANCE_GRADES = {"大超過", "小超過", "予算内"}

results = []


def check(label: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    msg = f"[{status}] {label}"
    if detail:
        msg += f" -- {detail}"
    print(msg)
    results.append(passed)


# -------------------------------------------------------------------
# 1. ファイル存在チェック
# -------------------------------------------------------------------
if not CSV_PATH.exists():
    print(f"[FAIL] CSV ファイルが存在しない: {CSV_PATH}")
    sys.exit(1)

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# -------------------------------------------------------------------
# 2. 行数チェック (420行以上)
# -------------------------------------------------------------------
check("行数 >= 420", len(df) >= 420, f"実際: {len(df)} 行")

# -------------------------------------------------------------------
# 3. 必須列の存在チェック
# -------------------------------------------------------------------
missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
check("必須列が全て存在する", len(missing_cols) == 0, f"不足: {missing_cols}")

# -------------------------------------------------------------------
# 4. record_date の形式チェック (YYYY-MM-DD)
# -------------------------------------------------------------------
if "record_date" in df.columns:
    invalid_dates = df["record_date"].dropna().apply(
        lambda v: not str(v).strip()[:10].replace("-", "").isdigit()
    )
    check("record_date が YYYY-MM-DD 形式", not invalid_dates.any(),
          f"不正件数: {invalid_dates.sum()}")
else:
    check("record_date 列が存在する", False)

# -------------------------------------------------------------------
# 5. record_id の一意性チェック
# -------------------------------------------------------------------
if "record_id" in df.columns:
    dup_count = df["record_id"].duplicated().sum()
    check("record_id が一意", dup_count == 0, f"重複件数: {dup_count}")
else:
    check("record_id 列が存在する", False)

# -------------------------------------------------------------------
# 6. project_no の種類数 (4以上)
# -------------------------------------------------------------------
if "project_no" in df.columns:
    n_proj = df["project_no"].nunique()
    check("project_no の種類数 >= 4", n_proj >= 4, f"実際: {n_proj}")
else:
    check("project_no 列が存在する", False)

# -------------------------------------------------------------------
# 7. work_type が 4種類
# -------------------------------------------------------------------
if "work_type" in df.columns:
    wt_set = set(df["work_type"].dropna().unique())
    check("work_type が 4種類含む",
          len(wt_set & EXPECTED_WORK_TYPES) == 4,
          f"実際: {wt_set}")
else:
    check("work_type 列が存在する", False)

# -------------------------------------------------------------------
# 8. cost_category が 3種類
# -------------------------------------------------------------------
if "cost_category" in df.columns:
    cc_set = set(df["cost_category"].dropna().unique())
    check("cost_category が 3種類含む",
          len(cc_set & EXPECTED_COST_CATEGORIES) == 3,
          f"実際: {cc_set}")
else:
    check("cost_category 列が存在する", False)

# -------------------------------------------------------------------
# 9. budget_amount > 0
# -------------------------------------------------------------------
if "budget_amount" in df.columns:
    invalid_budget = (df["budget_amount"] <= 0).sum()
    check("budget_amount がすべて > 0", invalid_budget == 0, f"違反件数: {invalid_budget}")
else:
    check("budget_amount 列が存在する", False)

# -------------------------------------------------------------------
# 10. actual_amount > 0
# -------------------------------------------------------------------
if "actual_amount" in df.columns:
    invalid_actual = (df["actual_amount"] <= 0).sum()
    check("actual_amount がすべて > 0", invalid_actual == 0, f"違反件数: {invalid_actual}")
else:
    check("actual_amount 列が存在する", False)

# -------------------------------------------------------------------
# 11. is_over_budget が 0/1 のみ
# -------------------------------------------------------------------
if "is_over_budget" in df.columns:
    unique_ob = set(df["is_over_budget"].dropna().unique())
    check("is_over_budget が 0/1 のみ",
          unique_ob.issubset({0, 1}),
          f"実際の値: {unique_ob}")
else:
    check("is_over_budget 列が存在する", False)

# -------------------------------------------------------------------
# 12. variance 計算整合性 (actual - budget)
# -------------------------------------------------------------------
if all(c in df.columns for c in ("variance", "actual_amount", "budget_amount")):
    expected_var = (df["actual_amount"] - df["budget_amount"]).round(0)
    diff = (df["variance"] - expected_var).abs()
    check("variance = actual_amount - budget_amount (誤差<=1)",
          (diff <= 1.0).all(), f"最大誤差: {diff.max():.2f}")
else:
    check("variance 計算チェック用列が存在する", False)

# -------------------------------------------------------------------
# 13. budget_status が 2種類
# -------------------------------------------------------------------
if "budget_status" in df.columns:
    bs_set = set(df["budget_status"].dropna().unique())
    check("budget_status が 2種類含む",
          len(bs_set & EXPECTED_BUDGET_STATUSES) == 2,
          f"実際: {bs_set}")
else:
    check("budget_status 列が存在する", False)

# -------------------------------------------------------------------
# 14. variance_grade が 3種類
# -------------------------------------------------------------------
if "variance_grade" in df.columns:
    vg_set = set(df["variance_grade"].dropna().unique())
    check("variance_grade が 3種類含む",
          len(vg_set & EXPECTED_VARIANCE_GRADES) == 3,
          f"実際: {vg_set}")
else:
    check("variance_grade 列が存在する", False)

# -------------------------------------------------------------------
# 15. 欠損率 <= 15% (主要列)
# -------------------------------------------------------------------
key_cols = [c for c in ["record_date", "record_id", "project_no", "budget_amount", "actual_amount"] if c in df.columns]
if key_cols:
    max_missing_rate = df[key_cols].isna().mean().max()
    check("主要列の欠損率 <= 15%", max_missing_rate <= 0.15,
          f"最大欠損率: {max_missing_rate:.2%}")
else:
    check("主要列の欠損率チェック", False)

# -------------------------------------------------------------------
# 16. source_file の種類数 (3つのファイル)
# -------------------------------------------------------------------
if "source_file" in df.columns:
    n_files = df["source_file"].nunique()
    check("source_file の種類数 == 3 (3ファイル)", n_files == 3, f"実際: {n_files}")
else:
    check("source_file 列が存在する", False)

# -------------------------------------------------------------------
# 17. 超過件数 >= 1
# -------------------------------------------------------------------
if "is_over_budget" in df.columns:
    over_count = (df["is_over_budget"] == 1).sum()
    check("超過件数 >= 1", over_count >= 1, f"超過件数: {over_count}")
else:
    check("is_over_budget 列が存在する", False)

# -------------------------------------------------------------------
# 18. 予算内件数 >= 1
# -------------------------------------------------------------------
if "is_over_budget" in df.columns:
    within_count = (df["is_over_budget"] == 0).sum()
    check("予算内件数 >= 1", within_count >= 1, f"予算内件数: {within_count}")
else:
    check("is_over_budget 列が存在する", False)

# -------------------------------------------------------------------
# 結果サマリー
# -------------------------------------------------------------------
total = len(results)
passed = sum(results)
failed = total - passed

print(f"\nResult: {passed}/{total} checks passed")

if failed > 0:
    print(f"FAIL: {failed} 件の検証に失敗しました")
    sys.exit(1)
else:
    print("全チェック PASS")
    sys.exit(0)

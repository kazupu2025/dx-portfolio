import json
import re
import pandas as pd
from pathlib import Path

CONFIG = {
    "expected_department_count": 5,
    "expected_year": 2024,
    "expected_month": 1,
    "min_rows": 300,
    "max_rows": 800,
    "all_cols": [
        "date", "employee_id", "employee_name", "department",
        "expense_type", "amount", "budget", "receipt_no",
        "amount_imputed", "source_file",
    ],
}

OUTPUT_DIR = Path("output")
CSV_PATH = OUTPUT_DIR / "cleaned_expense_202401.csv"
LOG_PATH = OUTPUT_DIR / "cleansing_log.md"
results = []


def check(check_id, name, category, condition, detail="", fix_hint=""):
    status = "PASS" if condition else "FAIL"
    results.append({"id": check_id, "name": name, "category": category,
                    "status": status, "detail": "" if condition else detail,
                    "fix_hint": "" if condition else fix_hint})
    return condition


check(1, "csv_exists", "存在", CSV_PATH.exists(), f"{CSV_PATH} が存在しない", "cleanse.py を再実行")
check(2, "log_exists", "存在", LOG_PATH.exists(), f"{LOG_PATH} が存在しない", "cleanse.py を確認")

if not CSV_PATH.exists():
    output = {"passed": 0, "failed": 2, "all_passed": False, "results": results}
    (OUTPUT_DIR / "result.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(1)

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

missing_cols = [c for c in CONFIG["all_cols"] if c not in df.columns]
extra_cols = [c for c in df.columns if c not in CONFIG["all_cols"]]
check(3, "schema", "スキーマ", len(missing_cols) == 0 and len(extra_cols) == 0,
      f"欠落: {missing_cols}, 余分: {extra_cols}", "COLUMN_MAP/KEEP_COLS を確認")

for col_id, col, hint in [
    (4, "date",          "normalize_date() を確認"),
    (5, "department",    "extract_department() を確認"),
    (6, "employee_id",   "COLUMN_MAP を確認"),
    (7, "expense_type",  "COLUMN_MAP を確認"),
    (8, "amount",        "normalize_numeric() を確認"),
    (9, "budget",        "COLUMN_MAP を確認"),
]:
    nan_count = df[col].isna().sum() if col in df.columns else len(df)
    check(col_id, f"{col}_nan", "完全性", nan_count == 0, f"{col} NaN: {nan_count}", hint)

if "date" in df.columns:
    bad_dates = df["date"].dropna()[~df["date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")]
    check(10, "date_format", "値域", len(bad_dates) == 0, f"不正日付: {len(bad_dates)}", "normalize_date() を確認")
else:
    check(10, "date_format", "値域", False, "date 列なし", "cleanse.py を確認")

if "date" in df.columns:
    ym = f"{CONFIG['expected_year']}-{CONFIG['expected_month']:02d}"
    out_of = df["date"].dropna()[~df["date"].dropna().str.startswith(ym)]
    check(11, "date_range", "値域", len(out_of) == 0, f"{ym}以外: {len(out_of)}", "日付フィルタを確認")
else:
    check(11, "date_range", "値域", False, "date 列なし", "cleanse.py を確認")

if "amount" in df.columns:
    neg = (df["amount"] < 0).sum()
    check(12, "amount_nonneg", "値域", neg == 0, f"amount < 0: {neg}", "normalize_numeric() を確認")
else:
    check(12, "amount_nonneg", "値域", False, "amount 列なし", "COLUMN_MAP を確認")

if "budget" in df.columns:
    neg = (df["budget"] < 0).sum()
    check(13, "budget_nonneg", "値域", neg == 0, f"budget < 0: {neg}", "normalize_numeric() を確認")
else:
    check(13, "budget_nonneg", "値域", False, "budget 列なし", "COLUMN_MAP を確認")

actual_depts = df["department"].nunique() if "department" in df.columns else 0
check(14, "department_count", "網羅性",
      actual_depts == CONFIG["expected_department_count"],
      f"期待: {CONFIG['expected_department_count']}, 実際: {actual_depts}", "extract_department() を確認")

check(15, "row_count", "網羅性",
      CONFIG["min_rows"] <= len(df) <= CONFIG["max_rows"],
      f"行数: {len(df)} (期待: {CONFIG['min_rows']}〜{CONFIG['max_rows']})", "フィルタを確認")

dup = int(df.duplicated().sum())
check(16, "no_duplicates", "整合性", dup == 0, f"重複: {dup}", "drop_duplicates() を確認")

if "department" in df.columns:
    bad = [d for d in df["department"].unique() if not re.search(r'[ぁ-鿿々ー]{2,}', str(d))]
    check(17, "dept_name_format", "品質", len(bad) == 0, f"不正部門名: {bad}", "extract_department() を確認")
else:
    check(17, "dept_name_format", "品質", False, "department 列なし", "cleanse.py を確認")

if "expense_type" in df.columns:
    valid_types = {"交通費", "宿泊費", "接待費", "消耗品費", "通信費", "研修費"}
    invalid = [t for t in df["expense_type"].unique() if t not in valid_types]
    check(18, "expense_type_valid", "品質", len(invalid) == 0,
          f"不正費目: {invalid}", "COLUMN_MAP を確認")
else:
    check(18, "expense_type_valid", "品質", False, "expense_type 列なし", "COLUMN_MAP を確認")

passed = sum(1 for r in results if r["status"] == "PASS")
failed = len(results) - passed
output = {"passed": passed, "failed": failed, "all_passed": failed == 0, "results": results}
(OUTPUT_DIR / "result.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n{'='*52}\n  チェック結果: {passed}/{len(results)} PASS\n{'='*52}")
for r in results:
    icon = "PASS" if r["status"] == "PASS" else "FAIL"
    line = f"  [{icon}]  [{r['category']:4s}] #{r['id']:02d} {r['name']}"
    if r["detail"]:
        line += f"\n         -> {r['detail']}\n         HINT: {r['fix_hint']}"
    print(line)
print(f"\n  全18項目クリア!" if failed == 0 else f"\n  {failed}項目が失敗")

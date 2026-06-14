import json
import re
import pandas as pd
from pathlib import Path

with open("config.yml", encoding="utf-8") as f:
    import yaml
    config = yaml.safe_load(f)

OUTPUT_DIR = Path("output")
CSV_PATH = OUTPUT_DIR / "cleaned_attendance_202401.csv"
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

ALL_COLS = [
    "date", "employee_id", "employee_name", "department",
    "clock_in", "clock_out", "break_minutes", "paid_leave",
    "actual_work_hours", "overtime_hours", "clock_imputed", "source_file",
]
missing_cols = [c for c in ALL_COLS if c not in df.columns]
extra_cols = [c for c in df.columns if c not in ALL_COLS]
check(3, "schema", "スキーマ", len(missing_cols) == 0 and len(extra_cols) == 0,
      f"欠落: {missing_cols}, 余分: {extra_cols}", "COLUMN_MAP/KEEP_COLS を確認")

for col_id, col, hint in [
    (4, "date",           "normalize_date() を確認"),
    (5, "department",     "extract_department() を確認"),
    (6, "employee_id",    "COLUMN_MAP を確認"),
    (7, "clock_in",       "normalize_time() を確認"),
    (8, "clock_out",      "normalize_time() を確認"),
    (9, "actual_work_hours", "calc_work_hours() を確認"),
]:
    nan_count = df[col].isna().sum() if col in df.columns else len(df)
    check(col_id, f"{col}_nan", "完全性", nan_count == 0, f"{col} NaN: {nan_count}", hint)

if "date" in df.columns:
    bad_dates = df["date"].dropna()[~df["date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")]
    check(10, "date_format", "値域", len(bad_dates) == 0, f"不正日付: {len(bad_dates)}", "normalize_date() を確認")
else:
    check(10, "date_format", "値域", False, "date 列なし", "cleanse.py を確認")

ym = f"{config['expected_year']}-{config['expected_month']:02d}"
if "date" in df.columns:
    out_of = df["date"].dropna()[~df["date"].dropna().str.startswith(ym)]
    check(11, "date_range", "値域", len(out_of) == 0, f"{ym}以外: {len(out_of)}", "日付フィルタを確認")
else:
    check(11, "date_range", "値域", False, "date 列なし", "cleanse.py を確認")

if "clock_in" in df.columns:
    bad_ci = df["clock_in"].dropna()[~df["clock_in"].dropna().str.match(r"^\d{2}:\d{2}$")]
    check(12, "clock_in_format", "値域", len(bad_ci) == 0, f"不正出勤時刻: {len(bad_ci)}", "normalize_time() を確認")
else:
    check(12, "clock_in_format", "値域", False, "clock_in 列なし", "COLUMN_MAP を確認")

if "actual_work_hours" in df.columns:
    neg = (df["actual_work_hours"] < 0).sum()
    check(13, "work_hours_nonneg", "値域", neg == 0, f"actual_work_hours < 0: {neg}", "calc_work_hours() を確認")
    too_long = (df["actual_work_hours"] > 20).sum()
    check(14, "work_hours_max", "値域", too_long == 0, f"actual_work_hours > 20h: {too_long}", "時刻解析を確認")
else:
    check(13, "work_hours_nonneg", "値域", False, "actual_work_hours 列なし", "cleanse.py を確認")
    check(14, "work_hours_max", "値域", False, "actual_work_hours 列なし", "cleanse.py を確認")

if "overtime_hours" in df.columns:
    neg = (df["overtime_hours"] < 0).sum()
    check(15, "overtime_nonneg", "値域", neg == 0, f"overtime_hours < 0: {neg}", ".clip(lower=0) を確認")
else:
    check(15, "overtime_nonneg", "値域", False, "overtime_hours 列なし", "cleanse.py を確認")

actual_depts = df["department"].nunique() if "department" in df.columns else 0
check(16, "department_count", "網羅性",
      actual_depts == config["expected_department_count"],
      f"期待: {config['expected_department_count']}, 実際: {actual_depts}", "extract_department() を確認")

check(17, "row_count", "網羅性",
      config["min_rows"] <= len(df) <= config["max_rows"],
      f"行数: {len(df)} (期待: {config['min_rows']}〜{config['max_rows']})", "フィルタを確認")

dup = int(df.duplicated().sum())
check(18, "no_duplicates", "整合性", dup == 0, f"重複: {dup}", "drop_duplicates() を確認")

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
if failed > 0:
    raise SystemExit(1)

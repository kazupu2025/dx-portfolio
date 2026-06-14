import json
import re
import pandas as pd
from pathlib import Path
import yaml

BASE_DIR = Path(__file__).parent.parent
with open(BASE_DIR / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

OUTPUT_DIR = Path(__file__).parent
CSV_PATH = OUTPUT_DIR / "cleaned_visit_202401.csv"
LOG_PATH = OUTPUT_DIR / "cleansing_log.md"
results = []


def check(check_id, name, category, condition, detail="", fix_hint=""):
    status = "PASS" if condition else "FAIL"
    results.append({"id": check_id, "name": name, "category": category,
                    "status": status, "detail": "" if condition else detail,
                    "fix_hint": "" if condition else fix_hint})
    return condition


check(1, "csv_exists",  "存在", CSV_PATH.exists(), f"{CSV_PATH} が存在しない", "cleanse.py を再実行")
check(2, "log_exists",  "存在", LOG_PATH.exists(), f"{LOG_PATH} が存在しない", "cleanse.py を確認")

if not CSV_PATH.exists():
    out = {"passed": 0, "failed": 2, "all_passed": False, "results": results}
    (OUTPUT_DIR / "result.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(1)

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

ALL_COLS = [
    "date", "weekday", "patient_id", "department",
    "reception_time", "hour_slot", "wait_minutes",
    "visit_route", "is_long_wait", "time_imputed", "source_file",
]
missing_cols = [c for c in ALL_COLS if c not in df.columns]
extra_cols   = [c for c in df.columns  if c not in ALL_COLS]
check(3, "schema", "スキーマ", len(missing_cols) == 0 and len(extra_cols) == 0,
      f"欠落: {missing_cols}, 余分: {extra_cols}", "COLUMN_MAP/KEEP_COLS を確認")

for col_id, col, hint in [
    (4, "date",           "normalize_date() を確認"),
    (5, "department",     "extract_department() を確認"),
    (6, "patient_id",     "COLUMN_MAP を確認"),
    (7, "reception_time", "normalize_time() を確認"),
    (8, "hour_slot",      "extract_hour() を確認"),
    (9, "wait_minutes",   "normalize_numeric を確認"),
]:
    nan_count = df[col].isna().sum() if col in df.columns else len(df)
    check(col_id, f"{col}_nan", "完全性", nan_count == 0, f"{col} NaN: {nan_count}", hint)

ym = f"{config['expected_year']}-{config['expected_month']:02d}"
if "date" in df.columns:
    bad_dates = df["date"].dropna()[~df["date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")]
    check(10, "date_format", "値域", len(bad_dates) == 0, f"不正日付: {len(bad_dates)}", "normalize_date() を確認")
    out_of = df["date"].dropna()[~df["date"].dropna().str.startswith(ym)]
    check(11, "date_range",  "値域", len(out_of) == 0, f"{ym}以外: {len(out_of)}", "日付フィルタを確認")
else:
    check(10, "date_format", "値域", False, "date列なし", "cleanse.py を確認")
    check(11, "date_range",  "値域", False, "date列なし", "cleanse.py を確認")

if "hour_slot" in df.columns:
    bad_h = df["hour_slot"].dropna()[(df["hour_slot"].dropna() < 8) | (df["hour_slot"].dropna() > 18)]
    check(12, "hour_range", "値域", len(bad_h) == 0, f"8〜18時外: {len(bad_h)}", "normalize_time() を確認")
else:
    check(12, "hour_range", "値域", False, "hour_slot列なし", "cleanse.py を確認")

if "wait_minutes" in df.columns:
    neg_w = (df["wait_minutes"] < 0).sum()
    check(13, "wait_nonneg", "値域", neg_w == 0, f"wait_minutes < 0: {neg_w}", "clip(lower=0) を確認")
else:
    check(13, "wait_nonneg", "値域", False, "wait_minutes列なし", "cleanse.py を確認")

actual_depts = df["department"].nunique() if "department" in df.columns else 0
check(14, "dept_count", "網羅性",
      actual_depts == config["expected_department_count"],
      f"期待: {config['expected_department_count']}, 実際: {actual_depts}", "extract_department() を確認")

check(15, "row_count", "網羅性",
      config["min_rows"] <= len(df) <= config["max_rows"],
      f"行数: {len(df)} (期待: {config['min_rows']}〜{config['max_rows']})", "行数を確認")

dup = int(df.duplicated().sum())
check(16, "no_duplicates", "整合性", dup == 0, f"重複: {dup}", "drop_duplicates() を確認")

if "weekday" in df.columns:
    valid_wd = {"月", "火", "水", "木", "金", "土", "日"}
    bad_wd = [w for w in df["weekday"].dropna().unique() if w not in valid_wd]
    check(17, "weekday_valid", "品質", len(bad_wd) == 0, f"不正曜日: {bad_wd}", "weekday変換を確認")
else:
    check(17, "weekday_valid", "品質", False, "weekday列なし", "cleanse.py を確認")

if "department" in df.columns:
    bad_dept = [d for d in df["department"].unique() if not re.search(r'[ぁ-鿿々ー]{2,}', str(d))]
    check(18, "dept_name_format", "品質", len(bad_dept) == 0,
          f"不正診療科名: {bad_dept}", "extract_department() を確認")
else:
    check(18, "dept_name_format", "品質", False, "department列なし", "cleanse.py を確認")

passed = sum(1 for r in results if r["status"] == "PASS")
failed  = len(results) - passed
out = {"passed": passed, "failed": failed, "all_passed": failed == 0, "results": results}
(OUTPUT_DIR / "result.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n{'='*52}\n  チェック結果: {passed}/{len(results)} PASS\n{'='*52}")
for r in results:
    icon = "PASS" if r["status"] == "PASS" else "FAIL"
    line = f"  [{icon}]  [{r['category']:4s}] #{r['id']:02d} {r['name']}"
    if r["detail"]:
        line += f"\n         -> {r['detail']}\n         HINT: {r['fix_hint']}"
    print(line)
print(f"\n  全18項目クリア!" if failed == 0 else f"\n  {failed}項目が失敗")

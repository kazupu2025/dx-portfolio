import json
import re
import pandas as pd
from pathlib import Path
import yaml

with open("config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

OUTPUT_DIR = Path("output")
CSV_PATH = OUTPUT_DIR / "cleaned_inspection_202401.csv"
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
    "date", "product_code", "product_name", "process", "lot_no",
    "inspection_value", "lower_limit", "upper_limit", "unit",
    "inspector", "result", "is_defect", "value_imputed", "source_file",
]
missing_cols = [c for c in ALL_COLS if c not in df.columns]
extra_cols = [c for c in df.columns if c not in ALL_COLS]
check(3, "schema", "スキーマ", len(missing_cols) == 0 and len(extra_cols) == 0,
      f"欠落: {missing_cols}, 余分: {extra_cols}", "COLUMN_MAP/KEEP_COLS を確認")

for col_id, col, hint in [
    (4, "date",             "normalize_date() を確認"),
    (5, "process",          "extract_process() を確認"),
    (6, "product_code",     "COLUMN_MAP を確認"),
    (7, "inspection_value", "normalize_numeric() を確認"),
    (8, "lower_limit",      "normalize_numeric() を確認"),
    (9, "upper_limit",      "normalize_numeric() を確認"),
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

if "lower_limit" in df.columns and "upper_limit" in df.columns:
    invalid_limits = (df["lower_limit"] >= df["upper_limit"]).sum()
    check(12, "limits_valid", "整合性", invalid_limits == 0,
          f"下限≥上限: {invalid_limits}", "規格値を確認")
else:
    check(12, "limits_valid", "整合性", False, "limit列なし", "COLUMN_MAP を確認")

if "is_defect" in df.columns:
    defect_rate = df["is_defect"].mean()
    check(13, "defect_rate_reasonable", "品質",
          0 < defect_rate < 0.5,
          f"不良率が異常: {defect_rate:.3f}", "is_defect計算ロジックを確認")
else:
    check(13, "defect_rate_reasonable", "品質", False, "is_defect列なし", "cleanse.py を確認")

if "result" in df.columns:
    valid_results = {"OK", "NG"}
    invalid_r = df["result"].dropna()[~df["result"].isin(valid_results)]
    check(14, "result_valid", "品質", len(invalid_r) == 0,
          f"不正判定値: {invalid_r.unique().tolist()}", "result正規化を確認")
else:
    check(14, "result_valid", "品質", False, "result列なし", "cleanse.py を確認")

actual_procs = df["process"].nunique() if "process" in df.columns else 0
check(15, "process_count", "網羅性",
      actual_procs == config["expected_process_count"],
      f"期待: {config['expected_process_count']}, 実際: {actual_procs}", "extract_process() を確認")

check(16, "row_count", "網羅性",
      config["min_rows"] <= len(df) <= config["max_rows"],
      f"行数: {len(df)} (期待: {config['min_rows']}〜{config['max_rows']})", "フィルタを確認")

dup = int(df.duplicated().sum())
check(17, "no_duplicates", "整合性", dup == 0, f"重複: {dup}", "drop_duplicates() を確認")

if "process" in df.columns:
    bad_proc = [p for p in df["process"].unique() if not re.search(r'[ぁ-鿿々ー]{2,}', str(p))]
    check(18, "process_name_format", "品質", len(bad_proc) == 0,
          f"不正工程名: {bad_proc}", "extract_process() を確認")
else:
    check(18, "process_name_format", "品質", False, "process列なし", "cleanse.py を確認")

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

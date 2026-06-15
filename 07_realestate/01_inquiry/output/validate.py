import json
import re
import pandas as pd
from pathlib import Path
import yaml

CONFIG_PATH = Path(__file__).parent.parent / "config.yml"
with open(CONFIG_PATH, encoding="utf-8") as f:
    config = yaml.safe_load(f)

OUTPUT_DIR = Path(__file__).parent
CSV_PATH = OUTPUT_DIR / "cleaned_inquiry_202401.csv"
LOG_PATH = OUTPUT_DIR / "cleansing_log.md"
VALID_STAGES = set(config.get("stages", ["問い合わせ", "内見", "申し込み", "成約"]))
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
    out = {"passed": 0, "failed": 2, "all_passed": False, "results": results}
    (OUTPUT_DIR / "result.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(1)

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

ALL_COLS = [
    "date", "inquiry_id", "agent", "area", "property_type",
    "channel", "status", "is_contracted", "contract_amount",
    "amount_imputed", "source_file",
]
missing_cols = [c for c in ALL_COLS if c not in df.columns]
extra_cols   = [c for c in df.columns if c not in ALL_COLS]
check(3, "schema", "スキーマ", len(missing_cols) == 0 and len(extra_cols) == 0,
      f"欠落: {missing_cols}, 余分: {extra_cols}", "COLUMN_MAP/KEEP_COLS を確認")

for col_id, col, hint in [
    (4, "date",         "normalize_date() を確認"),
    (5, "area",         "extract_area() を確認"),
    (6, "inquiry_id",   "COLUMN_MAP を確認"),
    (7, "agent",        "COLUMN_MAP を確認"),
    (8, "status",       "STAGE_MAP を確認"),
    (9, "is_contracted","numeric変換を確認"),
]:
    nan_count = df[col].isna().sum() if col in df.columns else len(df)
    check(col_id, f"{col}_nan", "完全性", nan_count == 0, f"{col} NaN: {nan_count}", hint)

if "date" in df.columns:
    bad_dates = df["date"].dropna()[~df["date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")]
    check(10, "date_format", "値域", len(bad_dates) == 0, f"不正日付: {len(bad_dates)}", "normalize_date() を確認")
    ym = f"{config['expected_year']}-{config['expected_month']:02d}"
    out_of = df["date"].dropna()[~df["date"].dropna().str.startswith(ym)]
    check(11, "date_range", "値域", len(out_of) == 0, f"{ym}以外: {len(out_of)}", "日付フィルタを確認")
else:
    check(10, "date_format", "値域", False, "date列なし", "cleanse.py を確認")
    check(11, "date_range",  "値域", False, "date列なし", "cleanse.py を確認")

if "status" in df.columns:
    invalid_stages = [s for s in df["status"].unique() if s not in VALID_STAGES]
    check(12, "status_valid", "値域", len(invalid_stages) == 0,
          f"不正ステージ: {invalid_stages}", "STAGE_MAP を確認")
else:
    check(12, "status_valid", "値域", False, "status列なし", "cleanse.py を確認")

if "is_contracted" in df.columns:
    invalid_flag = df["is_contracted"][~df["is_contracted"].isin([0, 1])].count()
    check(13, "is_contracted_binary", "値域", invalid_flag == 0,
          f"0/1以外の値: {invalid_flag}", "astype(int) を確認")
else:
    check(13, "is_contracted_binary", "値域", False, "is_contracted列なし", "cleanse.py を確認")

if "contract_amount" in df.columns:
    neg_amt = (df["contract_amount"] < 0).sum()
    check(14, "amount_nonneg", "値域", neg_amt == 0, f"contract_amount < 0: {neg_amt}", "fillna(0) を確認")
else:
    check(14, "amount_nonneg", "値域", False, "contract_amount列なし", "cleanse.py を確認")

actual_areas = df["area"].nunique() if "area" in df.columns else 0
check(15, "area_count", "網羅性",
      actual_areas == config["expected_area_count"],
      f"期待: {config['expected_area_count']}, 実際: {actual_areas}", "extract_area() を確認")

check(16, "row_count", "網羅性",
      config["min_rows"] <= len(df) <= config["max_rows"],
      f"行数: {len(df)} (期待: {config['min_rows']}〜{config['max_rows']})", "行数を確認")

dup = int(df.duplicated().sum())
check(17, "no_duplicates", "整合性", dup == 0, f"重複: {dup}", "drop_duplicates() を確認")

if "is_contracted" in df.columns and "status" in df.columns:
    inconsistent = ((df["is_contracted"] == 1) & (df["status"] != "成約")).sum()
    check(18, "flag_status_consistent", "整合性", inconsistent == 0,
          f"is_contracted=1 だが status≠成約: {inconsistent}", "is_contracted/status の整合を確認")
else:
    check(18, "flag_status_consistent", "整合性", False, "列なし", "cleanse.py を確認")

passed = sum(1 for r in results if r["status"] == "PASS")
failed  = len(results) - passed
out_data = {"passed": passed, "failed": failed, "all_passed": failed == 0, "results": results}
(OUTPUT_DIR / "result.json").write_text(json.dumps(out_data, ensure_ascii=False, indent=2), encoding="utf-8")

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

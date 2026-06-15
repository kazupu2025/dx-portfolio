import json
import pandas as pd
from pathlib import Path
import yaml

with open("config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

OUTPUT_DIR = Path("output")
CSV_PATH   = OUTPUT_DIR / "cleaned_cost_202401.csv"
LOG_PATH   = OUTPUT_DIR / "cleansing_log.md"
results    = []


def check(check_id, name, category, condition, detail="", fix_hint=""):
    status = "PASS" if condition else "FAIL"
    results.append({"id": check_id, "name": name, "category": category,
                    "status": status, "detail": "" if condition else detail,
                    "fix_hint": "" if condition else fix_hint})
    return condition


# 1: csv_exists
check(1, "csv_exists", "存在", CSV_PATH.exists(),
      f"{CSV_PATH} が存在しない", "cleanse.py を再実行")

# 2: log_exists
check(2, "log_exists", "存在", LOG_PATH.exists(),
      f"{LOG_PATH} が存在しない", "cleanse.py を確認")

if not CSV_PATH.exists():
    out = {"passed": 0, "failed": len(results), "all_passed": False, "results": results}
    (OUTPUT_DIR / "result.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(1)

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

ALL_COLS = [
    "date", "store", "ingredient_code", "ingredient_name", "category",
    "purchase_qty", "unit_cost", "used_qty", "waste_qty",
    "purchase_cost", "waste_cost", "waste_rate",
    "qty_imputed", "source_file",
]
missing_cols = [c for c in ALL_COLS if c not in df.columns]
extra_cols   = [c for c in df.columns  if c not in ALL_COLS]

# 3: schema
check(3, "schema", "スキーマ", len(missing_cols) == 0 and len(extra_cols) == 0,
      f"欠落: {missing_cols}, 余分: {extra_cols}", "COLUMN_MAP/KEEP_COLS を確認")

# 4: date_nan
nan_date = df["date"].isna().sum() if "date" in df.columns else len(df)
check(4, "date_nan", "完全性", nan_date == 0,
      f"date NaN: {nan_date}", "normalize_date() を確認")

# 5: store_nan
nan_store = df["store"].isna().sum() if "store" in df.columns else len(df)
check(5, "store_nan", "完全性", nan_store == 0,
      f"store NaN: {nan_store}", "extract_store() を確認")

# 6: ingredient_code_nan
nan_ing = df["ingredient_code"].isna().sum() if "ingredient_code" in df.columns else len(df)
check(6, "ingredient_code_nan", "完全性", nan_ing == 0,
      f"ingredient_code NaN: {nan_ing}", "COLUMN_MAP を確認")

# 7: purchase_qty_nan
nan_pq = df["purchase_qty"].isna().sum() if "purchase_qty" in df.columns else len(df)
check(7, "purchase_qty_nan", "完全性", nan_pq == 0,
      f"purchase_qty NaN: {nan_pq}", "normalize_numeric() を確認")

# 8: unit_cost_nan
nan_uc = df["unit_cost"].isna().sum() if "unit_cost" in df.columns else len(df)
check(8, "unit_cost_nan", "完全性", nan_uc == 0,
      f"unit_cost NaN: {nan_uc}", "normalize_numeric() を確認")

# 9: waste_rate_nan
nan_wr = df["waste_rate"].isna().sum() if "waste_rate" in df.columns else len(df)
check(9, "waste_rate_nan", "完全性", nan_wr == 0,
      f"waste_rate NaN: {nan_wr}", "waste_rate計算を確認")

# 10: date_format
if "date" in df.columns:
    bad_dates = df["date"].dropna()[~df["date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")]
    check(10, "date_format", "値域", len(bad_dates) == 0,
          f"不正日付: {len(bad_dates)}", "normalize_date() を確認")
else:
    check(10, "date_format", "値域", False, "date列なし", "cleanse.py を確認")

# 11: date_range
if "date" in df.columns:
    ym = f"{config['expected_year']}-{config['expected_month']:02d}"
    out_of = df["date"].dropna()[~df["date"].dropna().str.startswith(ym)]
    check(11, "date_range", "値域", len(out_of) == 0,
          f"{ym}以外: {len(out_of)}", "日付フィルタを確認")
else:
    check(11, "date_range", "値域", False, "date列なし", "cleanse.py を確認")

# 12: purchase_qty_nonneg
if "purchase_qty" in df.columns:
    neg12 = (df["purchase_qty"] < 0).sum()
    check(12, "purchase_qty_nonneg", "値域", neg12 == 0,
          f"purchase_qty < 0: {neg12}", "clip(lower=0) を確認")
else:
    check(12, "purchase_qty_nonneg", "値域", False, "purchase_qty列なし", "cleanse.py を確認")

# 13: unit_cost_nonneg
if "unit_cost" in df.columns:
    neg13 = (df["unit_cost"] < 0).sum()
    check(13, "unit_cost_nonneg", "値域", neg13 == 0,
          f"unit_cost < 0: {neg13}", "clip(lower=0) を確認")
else:
    check(13, "unit_cost_nonneg", "値域", False, "unit_cost列なし", "cleanse.py を確認")

# 14: used_qty_nonneg
if "used_qty" in df.columns:
    neg14 = (df["used_qty"] < 0).sum()
    check(14, "used_qty_nonneg", "値域", neg14 == 0,
          f"used_qty < 0: {neg14}", "clip(lower=0) を確認")
else:
    check(14, "used_qty_nonneg", "値域", False, "used_qty列なし", "cleanse.py を確認")

# 15: waste_qty_nonneg
if "waste_qty" in df.columns:
    neg15 = (df["waste_qty"] < 0).sum()
    check(15, "waste_qty_nonneg", "値域", neg15 == 0,
          f"waste_qty < 0: {neg15}", "clip(lower=0) を確認")
else:
    check(15, "waste_qty_nonneg", "値域", False, "waste_qty列なし", "cleanse.py を確認")

# 16: purchase_cost_nonneg
if "purchase_cost" in df.columns:
    neg16 = (df["purchase_cost"] < 0).sum()
    check(16, "purchase_cost_nonneg", "値域", neg16 == 0,
          f"purchase_cost < 0: {neg16}", "派生列計算を確認")
else:
    check(16, "purchase_cost_nonneg", "値域", False, "purchase_cost列なし", "cleanse.py を確認")

# 17: store_count
actual_stores = df["store"].nunique() if "store" in df.columns else 0
check(17, "store_count", "網羅性",
      actual_stores == config["expected_store_count"],
      f"期待: {config['expected_store_count']}, 実際: {actual_stores}", "extract_store() を確認")

# 18: row_count
check(18, "row_count", "網羅性",
      config["min_rows"] <= len(df) <= config["max_rows"],
      f"行数: {len(df)} (期待: {config['min_rows']}〜{config['max_rows']})", "行数を確認")

passed = sum(1 for r in results if r["status"] == "PASS")
failed  = len(results) - passed
output = {"passed": passed, "failed": failed, "all_passed": failed == 0, "results": results}
(OUTPUT_DIR / "result.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n{'='*52}\n  チェック結果: {passed}/{len(results)} PASS\n{'='*52}")
for r in results:
    icon = "PASS" if r["status"] == "PASS" else "FAIL"
    line = f"  [{icon}]  [{r['category']:4s}] #{r['id']:02d} {r['name']}"
    if r["detail"]:
        line += f"\n         -> {r['detail']}\n         HINT: {r['fix_hint']}"
    print(line)
print(f"\n  全{len(results)}項目クリア!" if failed == 0 else f"\n  {failed}項目が失敗")
if failed > 0:
    raise SystemExit(1)

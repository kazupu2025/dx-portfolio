import json
import re
import pandas as pd
from pathlib import Path

CONFIG = {
    "expected_warehouse_count": 5,
    "expected_year": 2024,
    "expected_month": 1,
    "min_rows": 400,
    "max_rows": 1000,
    "max_imputed_ratio": 0.15,
    "all_cols": [
        "date", "warehouse", "item_code", "item_name", "category",
        "stock_qty", "min_stock_qty", "unit_cost", "received_qty", "shipped_qty",
        "stock_imputed", "source_file",
    ],
}

OUTPUT_DIR = Path("C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/05_logistics/01_inventory/output")
CSV_PATH = OUTPUT_DIR / "cleaned_inventory_202401.csv"
LOG_PATH = OUTPUT_DIR / "cleansing_log.md"

results = []


def check(check_id, name, category, condition, detail="", fix_hint=""):
    status = "PASS" if condition else "FAIL"
    results.append({
        "id": check_id, "name": name, "category": category,
        "status": status,
        "detail": "" if condition else detail,
        "fix_hint": "" if condition else fix_hint,
    })
    return condition


check(1, "csv_exists", "存在", CSV_PATH.exists(),
      f"{CSV_PATH} が存在しない", "cleanse.py を再実行する")
check(2, "log_exists", "存在", LOG_PATH.exists(),
      f"{LOG_PATH} が存在しない", "cleanse.py の出力処理を確認する")

if not CSV_PATH.exists():
    passed = sum(1 for r in results if r["status"] == "PASS")
    output = {"passed": passed, "failed": len(results) - passed,
              "all_passed": False, "results": results}
    (OUTPUT_DIR / "result.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print("FAIL: CSV が存在しないため早期終了")
    raise SystemExit(1)

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

missing_cols = [c for c in CONFIG["all_cols"] if c not in df.columns]
extra_cols = [c for c in df.columns if c not in CONFIG["all_cols"]]
check(3, "schema", "スキーマ",
      len(missing_cols) == 0 and len(extra_cols) == 0,
      f"欠落列: {missing_cols}, 余分な列: {extra_cols}",
      "cleanse.py の KEEP_COLS または COLUMN_MAP を確認")

for col_id, col, hint in [
    (4, "date",         "normalize_date() または日付列検出ロジックを確認"),
    (5, "warehouse",    "extract_warehouse_name() またはファイルグロブパターンを確認"),
    (6, "item_code",    "COLUMN_MAP に品目コード列名が登録されているか確認"),
    (7, "item_name",    "COLUMN_MAP に品目名列名が登録されているか確認"),
    (8, "stock_qty",    "normalize_numeric() または stock_qty 補完ロジックを確認"),
    (9, "min_stock_qty","COLUMN_MAP に最低在庫数列名が登録されているか確認"),
]:
    nan_count = df[col].isna().sum() if col in df.columns else len(df)
    check(col_id, f"{col}_nan", "完全性", nan_count == 0,
          f"{col} の NaN: {nan_count} 件", hint)

if "date" in df.columns:
    bad_dates = df["date"].dropna()[~df["date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")]
    check(10, "date_format", "値域", len(bad_dates) == 0,
          f"YYYY-MM-DD 形式でない date: {len(bad_dates)} 件",
          "normalize_date() のフォーマットリストを確認")
else:
    check(10, "date_format", "値域", False, "date 列が存在しない", "cleanse.py を確認")

if "date" in df.columns:
    year_month = f"{CONFIG['expected_year']}-{CONFIG['expected_month']:02d}"
    out_of_range = df["date"].dropna()[~df["date"].dropna().str.startswith(year_month)]
    check(11, "date_range", "値域", len(out_of_range) == 0,
          f"{year_month} 以外の日付: {len(out_of_range)} 件",
          "ソースファイルの日付列またはフィルタロジックを確認")
else:
    check(11, "date_range", "値域", False, "date 列が存在しない", "cleanse.py を確認")

if "stock_qty" in df.columns:
    neg = (df["stock_qty"] < 0).sum()
    check(12, "stock_qty_nonneg", "値域", neg == 0,
          f"stock_qty < 0: {neg} 件",
          "normalize_numeric() またはソースデータを確認")
else:
    check(12, "stock_qty_nonneg", "値域", False, "stock_qty 列が存在しない", "COLUMN_MAP を確認")

if "min_stock_qty" in df.columns:
    neg = (df["min_stock_qty"] < 0).sum()
    check(13, "min_stock_qty_nonneg", "値域", neg == 0,
          f"min_stock_qty < 0: {neg} 件",
          "normalize_numeric() またはソースデータを確認")
else:
    check(13, "min_stock_qty_nonneg", "値域", False, "min_stock_qty 列が存在しない", "COLUMN_MAP を確認")

if "unit_cost" in df.columns:
    neg = (df["unit_cost"] < 0).sum()
    check(14, "unit_cost_positive", "値域", neg == 0,
          f"unit_cost < 0: {neg} 件",
          "normalize_numeric() またはソースデータを確認")
else:
    check(14, "unit_cost_positive", "値域", False, "unit_cost 列が存在しない", "COLUMN_MAP を確認")

actual_warehouses = df["warehouse"].nunique() if "warehouse" in df.columns else 0
check(15, "warehouse_count", "網羅性",
      actual_warehouses == CONFIG["expected_warehouse_count"],
      f"期待: {CONFIG['expected_warehouse_count']} 倉庫, 実際: {actual_warehouses} 倉庫",
      "extract_warehouse_name() またはファイルグロブパターンを確認")

check(16, "row_count", "網羅性",
      CONFIG["min_rows"] <= len(df) <= CONFIG["max_rows"],
      f"行数: {len(df)} (期待: {CONFIG['min_rows']}〜{CONFIG['max_rows']})",
      "cleanse.py のフィルタロジックを確認（過剰除外の可能性）")

dup_count = int(df.duplicated().sum())
check(17, "no_duplicates", "整合性", dup_count == 0,
      f"完全重複行: {dup_count} 件", "cleanse.py に df.drop_duplicates() を追加")

if "warehouse" in df.columns:
    bad_names = [w for w in df["warehouse"].unique()
                 if not re.search(r'[ぁ-鿿々ー]{2,}', str(w))]
    check(18, "warehouse_name_format", "品質", len(bad_names) == 0,
          f"日本語を含まない倉庫名: {bad_names}",
          "extract_warehouse_name() を確認")
else:
    check(18, "warehouse_name_format", "品質", False,
          "warehouse 列が存在しない", "extract_warehouse_name() を確認")

passed = sum(1 for r in results if r["status"] == "PASS")
failed = len(results) - passed
output = {"passed": passed, "failed": failed, "all_passed": failed == 0, "results": results}
(OUTPUT_DIR / "result.json").write_text(
    json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n{'='*52}")
print(f"  チェック結果: {passed}/{len(results)} PASS")
print(f"{'='*52}")
for r in results:
    icon = "PASS" if r["status"] == "PASS" else "FAIL"
    line = f"  [{icon}]  [{r['category']:4s}] #{r['id']:02d} {r['name']}"
    if r["detail"]:
        line += f"\n         -> {r['detail']}"
        line += f"\n         HINT: {r['fix_hint']}"
    print(line)

if failed == 0:
    print("\n  全18項目クリア!")
else:
    print(f"\n  {failed}項目が失敗。result.json の fix_hint を参照してください。")

"""
売上データ品質チェックリスト（20項目）- 飲食業 A-02 版
"""
import json
import pandas as pd
from pathlib import Path

CONFIG = {
    "expected_store_count": 5,
    "expected_year": 2024,
    "expected_month": 1,
    "min_rows": 500,
    "max_rows": 1200,
    "max_imputed_ratio": 0.15,
    "price_mismatch_tolerance": 1.0,
    "waste_loss_alert_threshold": 0.05,
    "all_cols": ["date", "store_name", "item_name", "category",
                 "quantity", "unit_price", "sales_amount",
                 "waste_qty", "waste_amount",
                 "sales_imputed", "source_file"],
    "store_name_exceptions": [],
}

OUTPUT_DIR = Path("output")
CSV_PATH = OUTPUT_DIR / "cleaned_sales_202401.csv"
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
    (5, "sales_amount", "normalize_numeric() または sales_amount 補完ロジックを確認"),
    (6, "store_name",   "extract_store_name() またはファイルグロブパターンを確認"),
    (7, "waste_qty",    "COLUMN_MAP に廃棄数量列名が登録されているか確認"),
    (8, "waste_amount", "COLUMN_MAP に廃棄金額列名が登録されているか確認"),
]:
    nan_count = df[col].isna().sum() if col in df.columns else len(df)
    check(col_id, f"{col}_nan", "完全性", nan_count == 0,
          f"{col} の NaN: {nan_count} 件", hint)

if "date" in df.columns:
    bad_dates = df["date"].dropna()[~df["date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")]
    check(9, "date_format", "値域", len(bad_dates) == 0,
          f"YYYY-MM-DD 形式でない date: {len(bad_dates)} 件",
          "normalize_date() のフォーマットリストを確認")
else:
    check(9, "date_format", "値域", False, "date 列が存在しない", "cleanse.py を確認")

if "date" in df.columns:
    year_month = f"{CONFIG['expected_year']}-{CONFIG['expected_month']:02d}"
    out_of_range = df["date"].dropna()[~df["date"].dropna().str.startswith(year_month)]
    check(10, "date_range", "値域", len(out_of_range) == 0,
          f"{year_month} 以外の日付: {len(out_of_range)} 件",
          "ソースファイルの日付列またはフィルタロジックを確認")
else:
    check(10, "date_range", "値域", False, "date 列が存在しない", "cleanse.py を確認")

if "sales_amount" in df.columns:
    neg = (df["sales_amount"] < 0).sum()
    check(11, "sales_amount_positive", "値域", neg == 0,
          f"sales_amount < 0: {neg} 件",
          "normalize_numeric() またはソースデータを確認")
else:
    check(11, "sales_amount_positive", "値域", False, "sales_amount 列が存在しない", "COLUMN_MAP を確認")

neg_detail = []
for col in ["quantity", "unit_price"]:
    if col in df.columns:
        n = (df[col].dropna() < 0).sum()
        if n:
            neg_detail.append(f"{col}: {n}件")
check(12, "numeric_positive", "値域", len(neg_detail) == 0,
      f"負値あり: {neg_detail}", "normalize_numeric() またはソースデータを確認")

if "waste_qty" in df.columns:
    neg_waste = (df["waste_qty"] < 0).sum()
    check(13, "waste_qty_nonneg", "値域", neg_waste == 0,
          f"waste_qty < 0: {neg_waste} 件",
          "waste_qty の normalize_numeric() ロジックを確認")
else:
    check(13, "waste_qty_nonneg", "値域", False,
          "waste_qty 列が存在しない", "COLUMN_MAP に廃棄数量列名を追加する")

if "waste_amount" in df.columns:
    neg_waste_amt = (df["waste_amount"] < 0).sum()
    check(14, "waste_amount_nonneg", "値域", neg_waste_amt == 0,
          f"waste_amount < 0: {neg_waste_amt} 件",
          "waste_amount の normalize_numeric() ロジックを確認")
else:
    check(14, "waste_amount_nonneg", "値域", False,
          "waste_amount 列が存在しない", "COLUMN_MAP に廃棄金額列名を追加する")

actual_stores = df["store_name"].nunique() if "store_name" in df.columns else 0
check(15, "store_count", "網羅性",
      actual_stores == CONFIG["expected_store_count"],
      f"期待: {CONFIG['expected_store_count']} 店舗, 実際: {actual_stores} 店舗",
      "extract_store_name() または STORE_NAME_MAP を確認")

if "store_name" in df.columns and "sales_amount" in df.columns:
    store_totals = df.groupby("store_name")["sales_amount"].sum()
    zero_stores = store_totals[store_totals == 0].index.tolist()
    check(16, "store_sales_nonzero", "網羅性", len(zero_stores) == 0,
          f"売上合計0の店舗: {zero_stores}",
          "COLUMN_MAP に売上金額列名が登録されているか確認")
else:
    check(16, "store_sales_nonzero", "網羅性", False,
          "store_name または sales_amount 列が不足", "cleanse.py の COLUMN_MAP を確認")

check(17, "row_count", "網羅性",
      CONFIG["min_rows"] <= len(df) <= CONFIG["max_rows"],
      f"行数: {len(df)} (期待: {CONFIG['min_rows']}〜{CONFIG['max_rows']})",
      "cleanse.py のフィルタロジックを確認（過剰除外の可能性）")

if {"unit_price", "quantity", "sales_amount"} <= set(df.columns):
    chk = df.dropna(subset=["unit_price", "quantity"])
    mismatch = (abs(chk["unit_price"] * chk["quantity"] - chk["sales_amount"])
                > CONFIG["price_mismatch_tolerance"]).sum()
    check(18, "price_consistency", "整合性", mismatch == 0,
          f"unit_price x quantity != sales_amount: {mismatch} 件",
          "normalize_numeric() または COLUMN_MAP を確認")
else:
    check(18, "price_consistency", "整合性", False,
          "unit_price / quantity / sales_amount 列が不足", "cleanse.py の COLUMN_MAP を確認")

dup_count = int(df.duplicated().sum())
check(19, "no_duplicates", "整合性", dup_count == 0,
      f"完全重複行: {dup_count} 件", "cleanse.py に df.drop_duplicates() を追加")

if "store_name" in df.columns:
    exceptions = set(CONFIG["store_name_exceptions"])
    bad_names = [s for s in df["store_name"].unique()
                 if not str(s).endswith("店") and s not in exceptions]
    check(20, "store_name_format", "品質", len(bad_names) == 0,
          f"「店」で終わらない店舗名: {bad_names}",
          "STORE_NAME_MAP に正規化ルールを追加")
else:
    check(20, "store_name_format", "品質", False,
          "store_name 列が存在しない", "extract_store_name() を確認")

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
    print("\n  全20項目クリア!")
else:
    print(f"\n  {failed}項目が失敗。result.json の fix_hint を参照してください。")

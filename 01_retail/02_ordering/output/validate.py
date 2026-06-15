"""
発注最適化・需要予測パイプライン
データ品質チェックリスト（18項目）
output/result.json に構造化結果を出力する
"""
import json
import pandas as pd
from pathlib import Path

_CONFIG_PATH = Path("config.yml")
if _CONFIG_PATH.exists():
    import yaml
    _yaml = yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8"))
else:
    _yaml = {}

CONFIG = {
    "expected_product_count":  _yaml.get("expected_product_count", 50),
    "expected_category_count": _yaml.get("expected_category_count", 5),
    "min_rows":  _yaml.get("min_rows", 4000),
    "max_rows":  _yaml.get("max_rows", 10000),
    "all_cols": [
        "date", "product_id", "product_name", "category",
        "sales_qty", "stock_qty", "reorder_point", "order_qty",
        "lead_time_days", "source_file",
    ],
}

OUTPUT_DIR = Path("output")
CSV_PATH = OUTPUT_DIR / "cleaned_order_2023Q4.csv"
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


# 1. csv_exists
check(1, "csv_exists", "存在", CSV_PATH.exists(),
      f"{CSV_PATH} が存在しない", "cleanse.py を再実行する")

# 2. log_exists
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

# 3. schema
missing_cols = [c for c in CONFIG["all_cols"] if c not in df.columns]
extra_cols = [c for c in df.columns if c not in CONFIG["all_cols"]]
check(3, "schema", "スキーマ",
      len(missing_cols) == 0 and len(extra_cols) == 0,
      f"欠落列: {missing_cols}, 余分な列: {extra_cols}",
      "cleanse.py の KEEP_COLS または列名マッピングを確認")

# 4. date_nan
nan_date = df["date"].isna().sum() if "date" in df.columns else len(df)
check(4, "date_nan", "完全性", nan_date == 0,
      f"date の NaN: {nan_date} 件", "normalize_date() を確認")

# 5. product_id_nan
nan_pid = df["product_id"].isna().sum() if "product_id" in df.columns else len(df)
check(5, "product_id_nan", "完全性", nan_pid == 0,
      f"product_id の NaN: {nan_pid} 件", "COLUMN_MAP の商品ID列を確認")

# 6. category_nan
nan_cat = df["category"].isna().sum() if "category" in df.columns else len(df)
check(6, "category_nan", "完全性", nan_cat == 0,
      f"category の NaN: {nan_cat} 件", "COLUMN_MAP のカテゴリ列を確認")

# 7. sales_qty_nan
nan_sq = df["sales_qty"].isna().sum() if "sales_qty" in df.columns else len(df)
check(7, "sales_qty_nan", "完全性", nan_sq == 0,
      f"sales_qty の NaN: {nan_sq} 件", "数値補完ロジックを確認")

# 8. stock_qty_nan
nan_stk = df["stock_qty"].isna().sum() if "stock_qty" in df.columns else len(df)
check(8, "stock_qty_nan", "完全性", nan_stk == 0,
      f"stock_qty の NaN: {nan_stk} 件", "数値補完ロジックを確認")

# 9. date_format
if "date" in df.columns:
    bad_dates = df["date"].dropna()[~df["date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")]
    date_fmt_ok = len(bad_dates) == 0
    date_fmt_detail = f"YYYY-MM-DD 形式でない date: {len(bad_dates)} 件"
else:
    date_fmt_ok = False
    date_fmt_detail = "date 列が存在しない"
check(9, "date_format", "値域", date_fmt_ok, date_fmt_detail,
      "normalize_date() のフォーマットリストを確認")

# 10. date_range (2023-10 〜 2023-12)
if "date" in df.columns:
    dates = pd.to_datetime(df["date"].dropna(), errors="coerce")
    out_range = dates[(dates.dt.year != 2023) | (~dates.dt.month.isin([10, 11, 12]))]
    date_range_ok = len(out_range) == 0
    date_range_detail = f"2023-10〜12 以外の日付: {len(out_range)} 件"
else:
    date_range_ok = False
    date_range_detail = "date 列が存在しない"
check(10, "date_range", "値域", date_range_ok, date_range_detail,
      "ソースファイルの日付を確認")

# 11. sales_qty_nonneg
if "sales_qty" in df.columns:
    neg_sq = (pd.to_numeric(df["sales_qty"], errors="coerce") < 0).sum()
    check(11, "sales_qty_nonneg", "値域", neg_sq == 0,
          f"sales_qty < 0: {neg_sq} 件", "サンプルデータ生成ロジックを確認")
else:
    check(11, "sales_qty_nonneg", "値域", False, "sales_qty 列が存在しない", "")

# 12. stock_qty_nonneg
if "stock_qty" in df.columns:
    neg_stk = (pd.to_numeric(df["stock_qty"], errors="coerce") < 0).sum()
    check(12, "stock_qty_nonneg", "値域", neg_stk == 0,
          f"stock_qty < 0: {neg_stk} 件", "サンプルデータ生成ロジックを確認")
else:
    check(12, "stock_qty_nonneg", "値域", False, "stock_qty 列が存在しない", "")

# 13. order_qty_nonneg
if "order_qty" in df.columns:
    neg_oq = (pd.to_numeric(df["order_qty"], errors="coerce") < 0).sum()
    check(13, "order_qty_nonneg", "値域", neg_oq == 0,
          f"order_qty < 0: {neg_oq} 件", "サンプルデータ生成ロジックを確認")
else:
    check(13, "order_qty_nonneg", "値域", False, "order_qty 列が存在しない", "")

# 14. lead_time_days_nonneg
if "lead_time_days" in df.columns:
    neg_lt = (pd.to_numeric(df["lead_time_days"], errors="coerce") < 0).sum()
    check(14, "lead_time_days_nonneg", "値域", neg_lt == 0,
          f"lead_time_days < 0: {neg_lt} 件", "サンプルデータ生成ロジックを確認")
else:
    check(14, "lead_time_days_nonneg", "値域", False, "lead_time_days 列が存在しない", "")

# 15. category_count
actual_cats = df["category"].nunique() if "category" in df.columns else 0
check(15, "category_count", "網羅性",
      actual_cats == CONFIG["expected_category_count"],
      f"期待: {CONFIG['expected_category_count']} カテゴリ, 実際: {actual_cats}",
      "サンプルデータ生成またはCOLUMN_MAPを確認")

# 16. product_count
actual_prods = df["product_id"].nunique() if "product_id" in df.columns else 0
check(16, "product_count", "網羅性",
      actual_prods == CONFIG["expected_product_count"],
      f"期待: {CONFIG['expected_product_count']} 商品, 実際: {actual_prods}",
      "サンプルデータ生成を確認")

# 17. no_future_dates
if "date" in df.columns:
    dates2 = pd.to_datetime(df["date"].dropna(), errors="coerce")
    future = dates2[dates2.dt.year >= 2024]
    check(17, "no_future_dates", "値域", len(future) == 0,
          f"2024年以降の日付: {len(future)} 件", "date_range フィルタを確認")
else:
    check(17, "no_future_dates", "値域", False, "date 列が存在しない", "")

# 18. row_count
check(18, "row_count", "網羅性",
      CONFIG["min_rows"] <= len(df) <= CONFIG["max_rows"],
      f"行数: {len(df)} (期待: {CONFIG['min_rows']}〜{CONFIG['max_rows']})",
      "cleanse.py のフィルタロジックを確認")

# ── 結果出力 ──────────────────────────────────────────────────────────
passed = sum(1 for r in results if r["status"] == "PASS")
failed = len(results) - passed

output = {
    "passed": passed,
    "failed": failed,
    "all_passed": failed == 0,
    "results": results,
}
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

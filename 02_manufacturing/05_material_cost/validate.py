import json
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
CSV_PATH = OUTPUT_DIR / "cleaned_material_202401.csv"
RESULT_PATH = OUTPUT_DIR / "result.json"

results = []


def check(check_id, name, category, condition, detail="", fix_hint=""):
    status = "PASS" if condition else "FAIL"
    results.append({
        "id": check_id,
        "name": name,
        "category": category,
        "status": status,
        "detail": "" if condition else detail,
        "fix_hint": "" if condition else fix_hint,
    })
    return condition


# 1: CSV存在確認
check(1, "csv_exists", "存在", CSV_PATH.exists(),
      f"{CSV_PATH} が存在しない", "cleanse.py を再実行")

if not CSV_PATH.exists():
    out = {"passed": 0, "failed": len(results), "all_passed": False, "results": results}
    RESULT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(1)

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

REQUIRED_COLS = [
    "purchase_date", "material_code", "material_name", "category",
    "supplier", "quantity", "unit_price", "prev_month_price",
    "price_change_rate", "total_cost", "price_change_flag", "source_file",
]
missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]

# 2: 行数 >= 400
check(2, "row_count_min", "網羅性", len(df) >= 400,
      f"行数 {len(df)} < 400", "_gen_sample_data.py を確認")

# 3: 必須列の存在
check(3, "required_columns", "スキーマ", len(missing_cols) == 0,
      f"欠落列: {missing_cols}", "cleanse.py の COLUMN_MAP を確認")

# 4: 日付フォーマット YYYY-MM-DD
if "purchase_date" in df.columns:
    bad_dates = df["purchase_date"].dropna()[
        ~df["purchase_date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")
    ]
    check(4, "date_format", "値域", len(bad_dates) == 0,
          f"不正日付 {len(bad_dates)} 件", "normalize_date() を確認")
else:
    check(4, "date_format", "値域", False, "purchase_date 列なし", "cleanse.py を確認")

# 5: material_codeが10種類以上
n_mat = df["material_code"].nunique() if "material_code" in df.columns else 0
check(5, "material_code_variety", "網羅性", n_mat >= 10,
      f"material_code の種類 {n_mat} < 10", "_gen_sample_data.py を確認")

# 6: categoryが4種類
n_cat = df["category"].nunique() if "category" in df.columns else 0
check(6, "category_count", "網羅性", n_cat == 4,
      f"category の種類 {n_cat} (期待: 4)", "_gen_sample_data.py を確認")

# 7: supplierが5種類
n_sup = df["supplier"].nunique() if "supplier" in df.columns else 0
check(7, "supplier_count", "網羅性", n_sup == 5,
      f"supplier の種類 {n_sup} (期待: 5)", "_gen_sample_data.py を確認")

# 8: unit_price > 0
if "unit_price" in df.columns:
    n_zero_up = (df["unit_price"] <= 0).sum()
    check(8, "unit_price_positive", "値域", n_zero_up == 0,
          f"unit_price <= 0 が {n_zero_up} 件", "clip(lower=0) を確認")
else:
    check(8, "unit_price_positive", "値域", False, "unit_price 列なし", "cleanse.py を確認")

# 9: prev_month_price > 0
if "prev_month_price" in df.columns:
    n_zero_pp = (df["prev_month_price"] <= 0).sum()
    check(9, "prev_month_price_positive", "値域", n_zero_pp == 0,
          f"prev_month_price <= 0 が {n_zero_pp} 件", "_gen_sample_data.py を確認")
else:
    check(9, "prev_month_price_positive", "値域", False, "prev_month_price 列なし", "cleanse.py を確認")

# 10: quantity > 0
if "quantity" in df.columns:
    n_zero_q = (df["quantity"] <= 0).sum()
    check(10, "quantity_positive", "値域", n_zero_q == 0,
          f"quantity <= 0 が {n_zero_q} 件", "clip(lower=0) を確認")
else:
    check(10, "quantity_positive", "値域", False, "quantity 列なし", "cleanse.py を確認")

# 11: total_cost = quantity * unit_price の整合性（許容誤差1円）
if all(c in df.columns for c in ["total_cost", "quantity", "unit_price"]):
    expected_tc = (df["quantity"] * df["unit_price"]).round(0)
    diff = (df["total_cost"] - expected_tc).abs()
    n_mismatch = (diff > 1).sum()
    check(11, "total_cost_consistency", "整合性", n_mismatch == 0,
          f"total_cost 不整合 {n_mismatch} 件 (許容誤差 1 円)", "cleanse.py の計算式を確認")
else:
    check(11, "total_cost_consistency", "整合性", False, "必要列なし", "cleanse.py を確認")

# 12: price_change_rateの範囲 (-1.0 <= r <= 2.0)
if "price_change_rate" in df.columns:
    valid_pcr = df["price_change_rate"].dropna()
    n_out = ((valid_pcr < -1.0) | (valid_pcr > 2.0)).sum()
    check(12, "price_change_rate_range", "値域", n_out == 0,
          f"price_change_rate が範囲外 {n_out} 件", "cleanse.py の計算を確認")
else:
    check(12, "price_change_rate_range", "値域", False, "price_change_rate 列なし", "cleanse.py を確認")

# 13: price_change_flagが"急騰"/"急落"/"安定"のみ
if "price_change_flag" in df.columns:
    valid_flags = {"急騰", "急落", "安定"}
    invalid_flags = set(df["price_change_flag"].dropna().unique()) - valid_flags
    check(13, "price_change_flag_values", "値域", len(invalid_flags) == 0,
          f"不正フラグ: {invalid_flags}", "cleanse.py の flag() 関数を確認")
else:
    check(13, "price_change_flag_values", "値域", False, "price_change_flag 列なし", "cleanse.py を確認")

# 14: source_file列の存在
check(14, "source_file_exists", "スキーマ", "source_file" in df.columns,
      "source_file 列なし", "cleanse.py を確認")

# 15: 欠損率 <= 15%
total_cells = df.shape[0] * df.shape[1]
missing_cells = df.isna().sum().sum()
missing_rate = missing_cells / total_cells if total_cells > 0 else 1.0
check(15, "missing_rate", "完全性", missing_rate <= 0.15,
      f"欠損率 {missing_rate*100:.2f}% > 15%", "cleanse.py のfillna処理を確認")

# 16: source_fileが3種類
n_src = df["source_file"].nunique() if "source_file" in df.columns else 0
check(16, "source_file_count", "網羅性", n_src == 3,
      f"source_file の種類 {n_src} (期待: 3)", "_gen_sample_data.py と data/ フォルダを確認")

# 17: 急騰件数 >= 1
if "price_change_flag" in df.columns:
    n_soar = (df["price_change_flag"] == "急騰").sum()
    check(17, "has_soar_records", "網羅性", n_soar >= 1,
          f"急騰が {n_soar} 件 (期待: >= 1)", "_gen_sample_data.py の変動率設定を確認")
else:
    check(17, "has_soar_records", "網羅性", False, "price_change_flag 列なし", "cleanse.py を確認")

# 18: 急落件数 >= 1
if "price_change_flag" in df.columns:
    n_drop = (df["price_change_flag"] == "急落").sum()
    check(18, "has_drop_records", "網羅性", n_drop >= 1,
          f"急落が {n_drop} 件 (期待: >= 1)", "_gen_sample_data.py の変動率設定を確認")
else:
    check(18, "has_drop_records", "網羅性", False, "price_change_flag 列なし", "cleanse.py を確認")

# --- 結果出力 ---
passed = sum(1 for r in results if r["status"] == "PASS")
failed = len(results) - passed
output = {"passed": passed, "failed": failed, "all_passed": failed == 0, "results": results}
OUTPUT_DIR.mkdir(exist_ok=True)
RESULT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n{'='*52}\n  Check result: {passed}/{len(results)} PASS\n{'='*52}")
for r in results:
    icon = "PASS" if r["status"] == "PASS" else "FAIL"
    line = f"  [{icon}]  [{r['category']:4s}] #{r['id']:02d} {r['name']}"
    if r["detail"]:
        line += f"\n         -> {r['detail']}\n         HINT: {r['fix_hint']}"
    print(line)
print(f"\n  All {len(results)} checks cleared!" if failed == 0 else f"\n  {failed} check(s) failed")
if failed > 0:
    raise SystemExit(1)

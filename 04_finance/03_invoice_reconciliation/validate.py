"""
C-26: 請求書突合・差異検出パイプライン クレンジング出力バリデーション
18項目チェック。[PASS]/[FAIL] のみ使用。絵文字・em-dash なし。
"""
import json
import re
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
CSV_PATH = OUTPUT_DIR / "cleaned_invoice_202401.csv"
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


# --- 1. CSVファイル存在確認 ---
check(1, "csv_exists", "存在",
      CSV_PATH.exists(),
      f"{CSV_PATH} が存在しない", "cleanse.py を再実行")

if not CSV_PATH.exists():
    output = {"passed": 0, "failed": 1, "all_passed": False, "results": results}
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(1)

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# --- 2. 行数 >= 400 ---
check(2, "row_count_gte_400", "網羅性",
      len(df) >= 400,
      f"行数: {len(df)} (期待: >= 400)", "サンプルデータを再生成")

# --- 3. 必須列の存在 ---
REQUIRED_COLS = [
    "invoice_no", "invoice_date", "client_code",
    "invoice_amount", "received_amount", "payment_type",
    "variance_amount", "match_status", "source_file",
]
missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
check(3, "required_columns", "スキーマ",
      len(missing_cols) == 0,
      f"欠落列: {missing_cols}", "COLUMN_MAP を確認")

# --- 4. invoice_no のユニーク性 ---
if "invoice_no" in df.columns:
    dup_count = df["invoice_no"].duplicated().sum()
    check(4, "invoice_no_unique", "整合性",
          dup_count == 0,
          f"重複 invoice_no: {dup_count} 件", "drop_duplicates() を確認")
else:
    check(4, "invoice_no_unique", "整合性", False, "invoice_no 列なし", "COLUMN_MAP を確認")

# --- 5. 日付フォーマット YYYY-MM-DD (invoice_date) ---
if "invoice_date" in df.columns:
    bad_dates = df["invoice_date"].dropna()
    bad_dates = bad_dates[~bad_dates.str.match(r"^\d{4}-\d{2}-\d{2}$")]
    check(5, "invoice_date_format", "フォーマット",
          len(bad_dates) == 0,
          f"不正日付: {len(bad_dates)} 件", "normalize_date() を確認")
else:
    check(5, "invoice_date_format", "フォーマット", False, "invoice_date 列なし", "COLUMN_MAP を確認")

# --- 6. client_code が 20 種類以上 ---
if "client_code" in df.columns:
    n_clients = df["client_code"].nunique()
    check(6, "client_code_variety", "網羅性",
          n_clients >= 20,
          f"得意先種類: {n_clients} (期待: >= 20)", "サンプルデータを確認")
else:
    check(6, "client_code_variety", "網羅性", False, "client_code 列なし", "COLUMN_MAP を確認")

# --- 7. invoice_amount > 0 (全行) ---
if "invoice_amount" in df.columns:
    df["invoice_amount"] = pd.to_numeric(df["invoice_amount"], errors="coerce")
    non_pos = (df["invoice_amount"] <= 0).sum()
    check(7, "invoice_amount_positive", "値域",
          non_pos == 0,
          f"invoice_amount <= 0: {non_pos} 件", "normalize_numeric() を確認")
else:
    check(7, "invoice_amount_positive", "値域", False, "invoice_amount 列なし", "COLUMN_MAP を確認")

# --- 8. received_amount >= 0 (全行) ---
if "received_amount" in df.columns:
    df["received_amount"] = pd.to_numeric(df["received_amount"], errors="coerce").fillna(0)
    neg_rec = (df["received_amount"] < 0).sum()
    check(8, "received_amount_nonneg", "値域",
          neg_rec == 0,
          f"received_amount < 0: {neg_rec} 件", "normalize_numeric() を確認")
else:
    check(8, "received_amount_nonneg", "値域", False, "received_amount 列なし", "COLUMN_MAP を確認")

# --- 9. payment_type が 3 種類 ---
if "payment_type" in df.columns:
    n_pay = df["payment_type"].nunique()
    check(9, "payment_type_three_kinds", "網羅性",
          n_pay >= 3,
          f"支払区分種類: {n_pay} (期待: >= 3)", "PAYMENT_MAP を確認")
else:
    check(9, "payment_type_three_kinds", "網羅性", False, "payment_type 列なし", "COLUMN_MAP を確認")

# --- 10. match_status が規定値のみ ---
VALID_STATUS = {"一致", "差異", "過払", "未入金"}
if "match_status" in df.columns:
    invalid_status = set(df["match_status"].dropna().unique()) - VALID_STATUS
    check(10, "match_status_valid_values", "値域",
          len(invalid_status) == 0,
          f"不正ステータス: {invalid_status}", "compute_match_status() を確認")
else:
    check(10, "match_status_valid_values", "値域", False, "match_status 列なし", "cleanse.py を確認")

# --- 11. variance_amount の整合性 (received - invoice, 許容誤差1円) ---
if "variance_amount" in df.columns and "invoice_amount" in df.columns and "received_amount" in df.columns:
    df["_calc_var"] = df["received_amount"] - df["invoice_amount"]
    inconsistent = (df["variance_amount"] - df["_calc_var"]).abs() > 1
    n_incon = inconsistent.sum()
    check(11, "variance_amount_consistency", "整合性",
          n_incon == 0,
          f"整合性エラー: {n_incon} 件", "variance_amount 計算ロジックを確認")
else:
    check(11, "variance_amount_consistency", "整合性", False, "必要列なし", "cleanse.py を確認")

# --- 12. 一致件数が全体の 70% 以上 ---
if "match_status" in df.columns:
    match_rate = (df["match_status"] == "一致").sum() / len(df)
    check(12, "match_rate_gte_70pct", "品質",
          match_rate >= 0.70,
          f"一致率: {match_rate:.1%} (期待: >= 70%)", "サンプルデータの差異パターンを確認")
else:
    check(12, "match_rate_gte_70pct", "品質", False, "match_status 列なし", "cleanse.py を確認")

# --- 13. 差異件数 >= 1 ---
if "match_status" in df.columns:
    n_diff = (df["match_status"] == "差異").sum()
    check(13, "diff_exists", "網羅性",
          n_diff >= 1,
          f"差異件数: {n_diff}", "サンプルデータを確認")
else:
    check(13, "diff_exists", "網羅性", False, "match_status 列なし", "cleanse.py を確認")

# --- 14. source_file 列の存在 ---
check(14, "source_file_exists", "スキーマ",
      "source_file" in df.columns,
      "source_file 列なし", "cleanse.py を確認")

# --- 15. 欠損率 <= 15% ---
if len(df) > 0:
    missing_rate = df[REQUIRED_COLS].isnull().sum().sum() / (len(df) * len(REQUIRED_COLS))
    check(15, "missing_rate_lte_15pct", "完全性",
          missing_rate <= 0.15,
          f"欠損率: {missing_rate:.1%} (期待: <= 15%)", "クレンジングロジックを確認")
else:
    check(15, "missing_rate_lte_15pct", "完全性", False, "データなし", "cleanse.py を確認")

# --- 16. source_file が 3 種類 ---
if "source_file" in df.columns:
    n_src = df["source_file"].nunique()
    check(16, "source_file_three_kinds", "網羅性",
          n_src >= 3,
          f"source_file 種類: {n_src} (期待: >= 3)", "全3スタイルCSVが存在するか確認")
else:
    check(16, "source_file_three_kinds", "網羅性", False, "source_file 列なし", "cleanse.py を確認")

# --- 17. 未入金件数 >= 1 ---
if "match_status" in df.columns:
    n_unpaid = (df["match_status"] == "未入金").sum()
    check(17, "unpaid_exists", "網羅性",
          n_unpaid >= 1,
          f"未入金件数: {n_unpaid}", "サンプルデータを確認")
else:
    check(17, "unpaid_exists", "網羅性", False, "match_status 列なし", "cleanse.py を確認")

# --- 18. 過払件数 >= 1 ---
if "match_status" in df.columns:
    n_over = (df["match_status"] == "過払").sum()
    check(18, "overpaid_exists", "網羅性",
          n_over >= 1,
          f"過払件数: {n_over}", "サンプルデータを確認")
else:
    check(18, "overpaid_exists", "網羅性", False, "match_status 列なし", "cleanse.py を確認")


# --- 結果出力 ---
passed = sum(1 for r in results if r["status"] == "PASS")
failed = len(results) - passed
output_data = {
    "passed": passed,
    "failed": failed,
    "all_passed": failed == 0,
    "results": results,
}
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n{'='*52}")
print(f"  チェック結果: {passed}/{len(results)} PASS")
print(f"{'='*52}")
for r in results:
    icon = "PASS" if r["status"] == "PASS" else "FAIL"
    line = f"  [{icon}]  [{r['category']:6s}] #{r['id']:02d} {r['name']}"
    if r["detail"]:
        line += f"\n           -> {r['detail']}"
        line += f"\n           HINT: {r['fix_hint']}"
    print(line)
print(f"\n  全{len(results)}項目クリア!" if failed == 0 else f"\n  {failed}項目が失敗")

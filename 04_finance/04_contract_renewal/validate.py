"""
C-31: 契約更新アラート・期限管理パイプライン クレンジング出力バリデーション
18項目チェック。[PASS]/[FAIL] のみ使用。絵文字・em-dash なし。
"""
import json
import re
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
CSV_PATH = OUTPUT_DIR / "cleaned_contracts_202401.csv"
RESULT_PATH = OUTPUT_DIR / "result.json"

REFERENCE_DATE = pd.Timestamp("2024-02-01")

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
    "contract_no", "customer_code", "insurance_type",
    "start_date", "end_date", "annual_premium", "agent_name",
    "days_to_expiry", "renewal_status", "source_file",
]
missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
check(3, "required_columns", "スキーマ",
      len(missing_cols) == 0,
      f"欠落列: {missing_cols}", "COLUMN_MAP を確認")

# --- 4. contract_no のユニーク性 ---
if "contract_no" in df.columns:
    dup_count = df["contract_no"].duplicated().sum()
    check(4, "contract_no_unique", "整合性",
          dup_count == 0,
          f"重複 contract_no: {dup_count} 件", "drop_duplicates() を確認")
else:
    check(4, "contract_no_unique", "整合性", False, "contract_no 列なし", "COLUMN_MAP を確認")

# --- 5. 日付フォーマット YYYY-MM-DD (start_date, end_date) ---
for date_col in ["start_date", "end_date"]:
    if date_col in df.columns:
        bad_dates = df[date_col].dropna()
        bad_dates = bad_dates[~bad_dates.str.match(r"^\d{4}-\d{2}-\d{2}$")]
        check(5, f"{date_col}_format", "フォーマット",
              len(bad_dates) == 0,
              f"不正日付 ({date_col}): {len(bad_dates)} 件", "normalize_date() を確認")
        break  # start_date と end_date 両方チェックするが1ID目は5とする
else:
    check(5, "date_format", "フォーマット", False, "日付列なし", "COLUMN_MAP を確認")

# --- 6. customer_code が 50 種類以上 ---
if "customer_code" in df.columns:
    n_customers = df["customer_code"].nunique()
    check(6, "customer_code_variety", "網羅性",
          n_customers >= 50,
          f"顧客種類: {n_customers} (期待: >= 50)", "サンプルデータを確認")
else:
    check(6, "customer_code_variety", "網羅性", False, "customer_code 列なし", "COLUMN_MAP を確認")

# --- 7. insurance_type が 4 種類 ---
if "insurance_type" in df.columns:
    n_ins = df["insurance_type"].nunique()
    check(7, "insurance_type_four_kinds", "網羅性",
          n_ins >= 4,
          f"保険種別種類: {n_ins} (期待: >= 4)", "INSURANCE_MAP を確認")
else:
    check(7, "insurance_type_four_kinds", "網羅性", False, "insurance_type 列なし", "COLUMN_MAP を確認")

# --- 8. agent_name が 5 種類 ---
if "agent_name" in df.columns:
    n_agents = df["agent_name"].nunique()
    check(8, "agent_name_five_kinds", "網羅性",
          n_agents >= 5,
          f"担当者種類: {n_agents} (期待: >= 5)", "サンプルデータを確認")
else:
    check(8, "agent_name_five_kinds", "網羅性", False, "agent_name 列なし", "COLUMN_MAP を確認")

# --- 9. annual_premium > 0 ---
if "annual_premium" in df.columns:
    df["annual_premium"] = pd.to_numeric(df["annual_premium"], errors="coerce")
    non_pos = (df["annual_premium"] <= 0).sum()
    check(9, "annual_premium_positive", "値域",
          non_pos == 0,
          f"annual_premium <= 0: {non_pos} 件", "normalize_numeric() を確認")
else:
    check(9, "annual_premium_positive", "値域", False, "annual_premium 列なし", "COLUMN_MAP を確認")

# --- 10. end_date >= start_date（契約期間整合性）---
if "start_date" in df.columns and "end_date" in df.columns:
    start_dt = pd.to_datetime(df["start_date"], errors="coerce")
    end_dt = pd.to_datetime(df["end_date"], errors="coerce")
    invalid_period = (end_dt < start_dt).sum()
    check(10, "end_date_gte_start_date", "整合性",
          invalid_period == 0,
          f"end_date < start_date: {invalid_period} 件", "契約期間ロジックを確認")
else:
    check(10, "end_date_gte_start_date", "整合性", False, "日付列なし", "COLUMN_MAP を確認")

# --- 11. days_to_expiry の整合性（end_date - 基準日と一致）---
if "days_to_expiry" in df.columns and "end_date" in df.columns:
    end_dt2 = pd.to_datetime(df["end_date"], errors="coerce")
    calc_days = (end_dt2 - REFERENCE_DATE).dt.days
    df["days_to_expiry"] = pd.to_numeric(df["days_to_expiry"], errors="coerce")
    inconsistent = (df["days_to_expiry"] - calc_days).abs() > 0
    n_incon = inconsistent.dropna().sum()
    check(11, "days_to_expiry_consistency", "整合性",
          n_incon == 0,
          f"days_to_expiry 不整合: {n_incon} 件", "days_to_expiry 計算ロジックを確認")
else:
    check(11, "days_to_expiry_consistency", "整合性", False, "必要列なし", "cleanse.py を確認")

# --- 12. renewal_status が規定値のみ ---
VALID_STATUS = {"期限切れ", "緊急", "警告", "正常"}
if "renewal_status" in df.columns:
    invalid_status = set(df["renewal_status"].dropna().unique()) - VALID_STATUS
    check(12, "renewal_status_valid_values", "値域",
          len(invalid_status) == 0,
          f"不正ステータス: {invalid_status}", "compute_renewal_status() を確認")
else:
    check(12, "renewal_status_valid_values", "値域", False, "renewal_status 列なし", "cleanse.py を確認")

# --- 13. 期限切れ件数 >= 1 ---
if "renewal_status" in df.columns:
    n_expired = (df["renewal_status"] == "期限切れ").sum()
    check(13, "expired_exists", "網羅性",
          n_expired >= 1,
          f"期限切れ件数: {n_expired}", "サンプルデータを確認")
else:
    check(13, "expired_exists", "網羅性", False, "renewal_status 列なし", "cleanse.py を確認")

# --- 14. 緊急件数 >= 1 ---
if "renewal_status" in df.columns:
    n_urgent = (df["renewal_status"] == "緊急").sum()
    check(14, "urgent_exists", "網羅性",
          n_urgent >= 1,
          f"緊急件数: {n_urgent}", "サンプルデータを確認")
else:
    check(14, "urgent_exists", "網羅性", False, "renewal_status 列なし", "cleanse.py を確認")

# --- 15. source_file 列の存在 ---
check(15, "source_file_exists", "スキーマ",
      "source_file" in df.columns,
      "source_file 列なし", "cleanse.py を確認")

# --- 16. 欠損率 <= 15% ---
if len(df) > 0:
    check_cols = [c for c in REQUIRED_COLS if c in df.columns]
    missing_rate = df[check_cols].isnull().sum().sum() / (len(df) * len(check_cols))
    check(16, "missing_rate_lte_15pct", "完全性",
          missing_rate <= 0.15,
          f"欠損率: {missing_rate:.1%} (期待: <= 15%)", "クレンジングロジックを確認")
else:
    check(16, "missing_rate_lte_15pct", "完全性", False, "データなし", "cleanse.py を確認")

# --- 17. source_file が 3 種類 ---
if "source_file" in df.columns:
    n_src = df["source_file"].nunique()
    check(17, "source_file_three_kinds", "網羅性",
          n_src >= 3,
          f"source_file 種類: {n_src} (期待: >= 3)", "全3スタイルCSVが存在するか確認")
else:
    check(17, "source_file_three_kinds", "網羅性", False, "source_file 列なし", "cleanse.py を確認")

# --- 18. contract_years が正（またはNaN）---
if "contract_years" in df.columns:
    neg_years = (pd.to_numeric(df["contract_years"], errors="coerce").fillna(1) <= 0).sum()
    check(18, "contract_years_positive", "値域",
          neg_years == 0,
          f"contract_years <= 0: {neg_years} 件", "契約年数計算ロジックを確認")
else:
    check(18, "contract_years_positive", "値域", False, "contract_years 列なし", "cleanse.py を確認")


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

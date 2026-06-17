# -*- coding: utf-8 -*-
"""
C-52: 保険契約問い合わせ・対応履歴分析パイプライン クレンジング出力バリデーション
18項目チェック。[PASS]/[FAIL] のみ使用。絵文字・em-dash なし。
"""
import json
import re
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
CSV_PATH = OUTPUT_DIR / "cleaned_inquiries_202401.csv"
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

# --- 2. 行数 >= 420 ---
check(2, "row_count_gte_420", "網羅性",
      len(df) >= 420,
      f"行数: {len(df)} (期待: >= 420)", "サンプルデータを再生成")

# --- 3. 必須列の存在 ---
REQUIRED_COLS = [
    "inquiry_date", "inquiry_id", "inquiry_type", "channel", "operator_id",
    "handling_minutes", "is_resolved", "recontact_flag", "satisfaction",
    "efficiency_flag", "cs_grade", "source_file",
]
missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
check(3, "required_columns", "スキーマ",
      len(missing_cols) == 0,
      f"欠落列: {missing_cols}", "COLUMN_MAP を確認")

# --- 4. inquiry_date フォーマット YYYY-MM-DD ---
if "inquiry_date" in df.columns:
    bad_dates = df["inquiry_date"].dropna()
    bad_dates = bad_dates[~bad_dates.str.match(r"^\d{4}-\d{2}-\d{2}$")]
    check(4, "inquiry_date_format", "フォーマット",
          len(bad_dates) == 0,
          f"不正日付: {len(bad_dates)} 件", "normalize_date() を確認")
else:
    check(4, "inquiry_date_format", "フォーマット", False, "inquiry_date 列なし", "COLUMN_MAP を確認")

# --- 5. inquiry_id の一意性 ---
if "inquiry_id" in df.columns:
    dup_count = df["inquiry_id"].duplicated().sum()
    check(5, "inquiry_id_unique", "整合性",
          dup_count == 0,
          f"重複 inquiry_id: {dup_count} 件", "drop_duplicates() を確認")
else:
    check(5, "inquiry_id_unique", "整合性", False, "inquiry_id 列なし", "COLUMN_MAP を確認")

# --- 6. inquiry_type が 5 種類 ---
if "inquiry_type" in df.columns:
    n_types = df["inquiry_type"].nunique()
    check(6, "inquiry_type_five_kinds", "網羅性",
          n_types >= 5,
          f"問い合わせ区分種類: {n_types} (期待: >= 5)", "TYPE_MAP を確認")
else:
    check(6, "inquiry_type_five_kinds", "網羅性", False, "inquiry_type 列なし", "COLUMN_MAP を確認")

# --- 7. channel が 3 種類 ---
if "channel" in df.columns:
    n_channels = df["channel"].nunique()
    check(7, "channel_three_kinds", "網羅性",
          n_channels >= 3,
          f"チャネル種類: {n_channels} (期待: >= 3)", "CHANNEL_MAP を確認")
else:
    check(7, "channel_three_kinds", "網羅性", False, "channel 列なし", "COLUMN_MAP を確認")

# --- 8. handling_minutes > 0 ---
if "handling_minutes" in df.columns:
    df["handling_minutes"] = pd.to_numeric(df["handling_minutes"], errors="coerce")
    non_pos = (df["handling_minutes"] <= 0).sum()
    check(8, "handling_minutes_positive", "値域",
          non_pos == 0,
          f"handling_minutes <= 0: {non_pos} 件", "数値変換を確認")
else:
    check(8, "handling_minutes_positive", "値域", False, "handling_minutes 列なし", "COLUMN_MAP を確認")

# --- 9. is_resolved が 0/1 のみ ---
if "is_resolved" in df.columns:
    df["is_resolved"] = pd.to_numeric(df["is_resolved"], errors="coerce")
    invalid_resolved = df["is_resolved"].dropna()
    invalid_resolved = invalid_resolved[~invalid_resolved.isin([0, 1])]
    check(9, "is_resolved_binary", "値域",
          len(invalid_resolved) == 0,
          f"不正 is_resolved 値: {len(invalid_resolved)} 件", "数値変換を確認")
else:
    check(9, "is_resolved_binary", "値域", False, "is_resolved 列なし", "COLUMN_MAP を確認")

# --- 10. recontact_flag が 0/1 のみ ---
if "recontact_flag" in df.columns:
    df["recontact_flag"] = pd.to_numeric(df["recontact_flag"], errors="coerce")
    invalid_recontact = df["recontact_flag"].dropna()
    invalid_recontact = invalid_recontact[~invalid_recontact.isin([0, 1])]
    check(10, "recontact_flag_binary", "値域",
          len(invalid_recontact) == 0,
          f"不正 recontact_flag 値: {len(invalid_recontact)} 件", "数値変換を確認")
else:
    check(10, "recontact_flag_binary", "値域", False, "recontact_flag 列なし", "COLUMN_MAP を確認")

# --- 11. satisfaction が 1〜5 ---
if "satisfaction" in df.columns:
    df["satisfaction"] = pd.to_numeric(df["satisfaction"], errors="coerce")
    invalid_sat = df["satisfaction"].dropna()
    invalid_sat = invalid_sat[(invalid_sat < 1) | (invalid_sat > 5)]
    check(11, "satisfaction_range", "値域",
          len(invalid_sat) == 0,
          f"範囲外 satisfaction: {len(invalid_sat)} 件", "データ生成を確認")
else:
    check(11, "satisfaction_range", "値域", False, "satisfaction 列なし", "COLUMN_MAP を確認")

# --- 12. efficiency_flag が 3 種類 ---
if "efficiency_flag" in df.columns:
    n_eff = df["efficiency_flag"].nunique()
    check(12, "efficiency_flag_three_kinds", "網羅性",
          n_eff >= 3,
          f"efficiency_flag 種類: {n_eff} (期待: >= 3)", "compute_efficiency_flag() を確認")
else:
    check(12, "efficiency_flag_three_kinds", "網羅性", False, "efficiency_flag 列なし", "cleanse.py を確認")

# --- 13. cs_grade が 3 種類 ---
if "cs_grade" in df.columns:
    n_grade = df["cs_grade"].nunique()
    check(13, "cs_grade_three_kinds", "網羅性",
          n_grade >= 3,
          f"cs_grade 種類: {n_grade} (期待: >= 3)", "compute_cs_grade() を確認")
else:
    check(13, "cs_grade_three_kinds", "網羅性", False, "cs_grade 列なし", "cleanse.py を確認")

# --- 14. 欠損率 <= 15% ---
if len(df) > 0:
    check_cols = [c for c in REQUIRED_COLS if c in df.columns]
    missing_rate = df[check_cols].isnull().sum().sum() / (len(df) * len(check_cols))
    check(14, "missing_rate_lte_15pct", "完全性",
          missing_rate <= 0.15,
          f"欠損率: {missing_rate:.1%} (期待: <= 15%)", "クレンジングロジックを確認")
else:
    check(14, "missing_rate_lte_15pct", "完全性", False, "データなし", "cleanse.py を確認")

# --- 15. source_file が 3 種類 ---
if "source_file" in df.columns:
    n_src = df["source_file"].nunique()
    check(15, "source_file_three_kinds", "網羅性",
          n_src >= 3,
          f"source_file 種類: {n_src} (期待: >= 3)", "全3スタイルCSVが存在するか確認")
else:
    check(15, "source_file_three_kinds", "網羅性", False, "source_file 列なし", "cleanse.py を確認")

# --- 16. 解決件数 >= 1 ---
if "is_resolved" in df.columns:
    n_resolved = (df["is_resolved"] == 1).sum()
    check(16, "resolved_exists", "網羅性",
          n_resolved >= 1,
          f"解決件数: {n_resolved}", "サンプルデータを確認")
else:
    check(16, "resolved_exists", "網羅性", False, "is_resolved 列なし", "cleanse.py を確認")

# --- 17. 未解決件数 >= 1 ---
if "is_resolved" in df.columns:
    n_unresolved = (df["is_resolved"] == 0).sum()
    check(17, "unresolved_exists", "網羅性",
          n_unresolved >= 1,
          f"未解決件数: {n_unresolved}", "サンプルデータを確認")
else:
    check(17, "unresolved_exists", "網羅性", False, "is_resolved 列なし", "cleanse.py を確認")

# --- 18. 再問い合わせ件数 >= 1 ---
if "recontact_flag" in df.columns:
    n_recontact = (df["recontact_flag"] == 1).sum()
    check(18, "recontact_exists", "網羅性",
          n_recontact >= 1,
          f"再問い合わせ件数: {n_recontact}", "サンプルデータを確認")
else:
    check(18, "recontact_exists", "網羅性", False, "recontact_flag 列なし", "cleanse.py を確認")


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
for r in results:
    icon = "PASS" if r["status"] == "PASS" else "FAIL"
    line = f"  [{icon}]  [{r['category']:6s}] #{r['id']:02d} {r['name']}"
    if r["detail"]:
        line += f"\n           -> {r['detail']}"
        line += f"\n           HINT: {r['fix_hint']}"
    print(line)
print(f"{'='*52}")
print(f"Result: {passed}/{len(results)} checks passed")

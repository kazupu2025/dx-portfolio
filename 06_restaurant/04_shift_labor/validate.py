# -*- coding: utf-8 -*-
"""
C-40: アルバイトシフト管理・人件費集計パイプライン
クレンジング出力バリデーションスクリプト（18項目チェック）
"""

import pandas as pd
from pathlib import Path
import sys

OUTPUT_DIR = Path(__file__).parent / "output"
TARGET_FILE = OUTPUT_DIR / "cleaned_shift_202401.csv"

REQUIRED_COLS = [
    "work_date", "staff_id", "store_name", "role",
    "start_time", "end_time", "work_hours", "hourly_rate",
    "daily_wage", "is_overtime", "labor_cost_flag", "source_file",
]


def check(label: str, result: bool, detail: str = "") -> bool:
    status = "[PASS]" if result else "[FAIL]"
    msg = f"{status} {label}"
    if detail:
        msg += f" | {detail}"
    print(msg)
    return result


def validate() -> bool:
    results = []

    # 1. CSVファイル存在確認
    file_exists = TARGET_FILE.exists()
    results.append(check("CSVファイル存在確認", file_exists, str(TARGET_FILE)))
    if not file_exists:
        print("[ERROR] ファイルが存在しないため残りのチェックをスキップします")
        return False

    df = pd.read_csv(TARGET_FILE, encoding="utf-8-sig")

    # 2. 行数 >= 420
    row_count = len(df)
    results.append(check("行数 >= 420", row_count >= 420, f"実際: {row_count} 行"))

    # 3. 必須列の存在
    missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
    results.append(check("必須列の存在", len(missing_cols) == 0, f"不足列: {missing_cols}"))

    if missing_cols:
        print("[ERROR] 必須列不足のため残りのチェックをスキップします")
        return False

    # 4. 日付フォーマット YYYY-MM-DD
    date_pattern = df["work_date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")
    results.append(check("日付フォーマット YYYY-MM-DD", date_pattern.all(),
                          f"不正行数: {(~date_pattern).sum()}"))

    # 5. staff_idが10種類以上
    staff_count = df["staff_id"].nunique()
    results.append(check("staff_id が 10 種類以上", staff_count >= 10,
                          f"実際: {staff_count} 種類"))

    # 6. store_nameが3種類
    store_count = df["store_name"].nunique()
    results.append(check("store_name が 3 種類", store_count == 3,
                          f"実際: {store_count} 種類 {df['store_name'].unique().tolist()}"))

    # 7. roleが3種類
    role_count = df["role"].nunique()
    results.append(check("role が 3 種類", role_count == 3,
                          f"実際: {role_count} 種類 {df['role'].unique().tolist()}"))

    # 8. work_hours > 0
    wh_positive = (pd.to_numeric(df["work_hours"], errors="coerce") > 0).all()
    results.append(check("work_hours > 0", wh_positive))

    # 9. hourly_rate >= 800（最低賃金チェック）
    hr_vals = pd.to_numeric(df["hourly_rate"], errors="coerce")
    hr_valid = (hr_vals >= 800).all()
    results.append(check("hourly_rate >= 800", hr_valid,
                          f"最小値: {hr_vals.min()}"))

    # 10. daily_wage > 0
    dw_positive = (pd.to_numeric(df["daily_wage"], errors="coerce") > 0).all()
    results.append(check("daily_wage > 0", dw_positive))

    # 11. is_overtimeが0または1のみ
    ot_vals = df["is_overtime"].unique()
    ot_valid = all(v in [0, 1] for v in ot_vals)
    results.append(check("is_overtime が 0 または 1 のみ", ot_valid,
                          f"実際の値: {sorted(ot_vals.tolist())}"))

    # 12. labor_cost_flagが"高コスト"/"標準"のみ
    flag_vals = df["labor_cost_flag"].unique()
    flag_valid = all(v in ["高コスト", "標準"] for v in flag_vals)
    results.append(check("labor_cost_flag が 高コスト/標準 のみ", flag_valid,
                          f"実際の値: {sorted(flag_vals.tolist())}"))

    # 13. source_file列の存在
    results.append(check("source_file 列の存在", "source_file" in df.columns))

    # 14. 欠損率 <= 15%
    total_cells = df.shape[0] * df.shape[1]
    null_cells = df.isnull().sum().sum()
    null_rate = null_cells / total_cells if total_cells > 0 else 0
    results.append(check("欠損率 <= 15%", null_rate <= 0.15,
                          f"欠損率: {null_rate:.2%}"))

    # 15. source_fileが3種類
    src_count = df["source_file"].nunique()
    results.append(check("source_file が 3 種類", src_count == 3,
                          f"実際: {src_count} 種類"))

    # 16. 残業シフト件数 >= 1（is_overtime=1）
    overtime_count = int((df["is_overtime"] == 1).sum())
    results.append(check("残業シフト件数 >= 1", overtime_count >= 1,
                          f"残業件数: {overtime_count}"))

    # 17. daily_wageの最大値 <= 50000
    dw_max = pd.to_numeric(df["daily_wage"], errors="coerce").max()
    results.append(check("daily_wage 最大値 <= 50000", dw_max <= 50000,
                          f"最大値: {dw_max}"))

    # 18. work_hoursの最大値 <= 24
    wh_max = pd.to_numeric(df["work_hours"], errors="coerce").max()
    results.append(check("work_hours 最大値 <= 24", wh_max <= 24,
                          f"最大値: {wh_max}"))

    passed = sum(results)
    total = len(results)
    print(f"\n結果: {passed}/{total} PASS")
    return passed == total


def main():
    print("=" * 60)
    print("クレンジング出力バリデーション (18 項目)")
    print("=" * 60)
    success = validate()
    print("=" * 60)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

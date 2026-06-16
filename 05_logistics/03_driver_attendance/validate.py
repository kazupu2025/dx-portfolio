"""
C-22 ドライバー勤怠・拘束時間管理パイプライン
クレンジング出力バリデーション（18項目以上）
"""
import sys
import re
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CSV_PATH = OUTPUT_DIR / "cleaned_driver_202401.csv"

REQUIRED_COLS = [
    "driver_id", "name", "office", "work_date",
    "departure_time", "return_time",
    "break_hours", "distance_km", "operation_type",
    "confinement_hours", "work_hours",
    "confinement_over_flag", "work_over_flag", "violation_flag",
    "source_file",
]

VALID_OFFICES = {"東京営業所", "大阪営業所", "名古屋営業所"}
VALID_OPERATION_TYPES = {"長距離", "中距離", "市内配送"}
VALID_VIOLATION_FLAGS = {"違反", "正常"}


def check(name: str, passed: bool, detail: str = "") -> bool:
    status = "PASS" if passed else "FAIL"
    msg = f"  [{status}] {name}"
    if detail:
        msg += f" - {detail}"
    print(msg)
    return passed


def main():
    results = []
    print("=" * 60)
    print("validate.py: クレンジング出力チェック")
    print("=" * 60)

    # 01 ファイル存在確認
    exists = CSV_PATH.exists()
    results.append(check("01 CSVファイル存在確認", exists, str(CSV_PATH)))
    if not exists:
        print("\n[ERROR] ファイルが存在しないため検証を中断します")
        sys.exit(1)

    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

    # 02 行数 >= 400
    results.append(check("02 行数 >= 400", len(df) >= 400, f"{len(df)} rows"))

    # 03 必須列の存在
    missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
    results.append(check("03 必須列の存在", len(missing_cols) == 0,
                         f"missing: {missing_cols}" if missing_cols else "all present"))
    if missing_cols:
        print("\n[ERROR] 必須列が不足しているため一部チェックをスキップします")
        sys.exit(1)

    # 04 work_date フォーマット YYYY-MM-DD
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    invalid_dates = df["work_date"].dropna().apply(
        lambda x: not bool(date_pattern.match(str(x)))
    ).sum()
    results.append(check("04 work_dateフォーマット YYYY-MM-DD", invalid_dates == 0,
                         f"不正件数: {invalid_dates}"))

    # 05 driver_idの種類 >= 20
    driver_count = df["driver_id"].nunique()
    results.append(check("05 driver_idの種類 >= 20", driver_count >= 20,
                         f"実際: {driver_count}種類"))

    # 06 officeの種類 == 3
    office_count = df["office"].nunique()
    results.append(check("06 officeの種類 == 3", office_count == 3,
                         f"実際: {office_count}種類"))

    # 07 operation_typeの種類 == 3
    op_count = df["operation_type"].nunique()
    results.append(check("07 operation_typeの種類 == 3", op_count == 3,
                         f"実際: {op_count}種類"))

    # 08 distance_km > 0
    neg_dist = (pd.to_numeric(df["distance_km"], errors="coerce") <= 0).sum()
    results.append(check("08 distance_km > 0", neg_dist == 0, f"非正値: {neg_dist}"))

    # 09 break_hours >= 0
    neg_break = (pd.to_numeric(df["break_hours"], errors="coerce") < 0).sum()
    results.append(check("09 break_hours >= 0", neg_break == 0, f"負値: {neg_break}"))

    # 10 confinement_hours > 0
    neg_conf = (pd.to_numeric(df["confinement_hours"], errors="coerce") <= 0).sum()
    results.append(check("10 confinement_hours > 0", neg_conf == 0, f"非正値: {neg_conf}"))

    # 11 work_hours > 0
    neg_work = (pd.to_numeric(df["work_hours"], errors="coerce") <= 0).sum()
    results.append(check("11 work_hours > 0", neg_work == 0, f"非正値: {neg_work}"))

    # 12 violation_flag の値域
    invalid_flag = (~df["violation_flag"].isin(VALID_VIOLATION_FLAGS)).sum()
    results.append(check("12 violation_flagの値域", invalid_flag == 0,
                         f"不正値: {invalid_flag}"))

    # 13 source_file 列の存在と非NULL
    sf_ok = ("source_file" in df.columns) and df["source_file"].notnull().all()
    results.append(check("13 source_file列の存在と非NULL", sf_ok))

    # 14 欠損率15%以下（必須列）
    null_rate = df[REQUIRED_COLS].isnull().mean().max()
    results.append(check("14 必須列の欠損率 <= 15%", null_rate <= 0.15,
                         f"最大欠損率: {null_rate:.1%}"))

    # 15 confinement_over_flag が bool/0/1
    conf_vals = df["confinement_over_flag"].dropna().unique()
    conf_ok = all(v in {True, False, 1, 0, "True", "False"} for v in conf_vals)
    results.append(check("15 confinement_over_flagの値域", conf_ok,
                         f"値: {set(str(v) for v in conf_vals)}"))

    # 16 work_over_flag が bool/0/1
    work_vals = df["work_over_flag"].dropna().unique()
    work_ok = all(v in {True, False, 1, 0, "True", "False"} for v in work_vals)
    results.append(check("16 work_over_flagの値域", work_ok,
                         f"値: {set(str(v) for v in work_vals)}"))

    # 17 officeが有効値のみ
    invalid_office = (~df["office"].isin(VALID_OFFICES)).sum()
    results.append(check("17 officeの値が有効", invalid_office == 0,
                         f"不正値: {invalid_office}"))

    # 18 operation_typeが有効値のみ
    invalid_op = (~df["operation_type"].isin(VALID_OPERATION_TYPES)).sum()
    results.append(check("18 operation_typeの値が有効", invalid_op == 0,
                         f"不正値: {invalid_op}"))

    # 19 違反フラグ整合性確認
    flag_conf = df["confinement_over_flag"].astype(bool)
    flag_work = df["work_over_flag"].astype(bool)
    expected_viol = (flag_conf | flag_work).map({True: "違反", False: "正常"})
    mismatch = (df["violation_flag"] != expected_viol).sum()
    results.append(check("19 violation_flagの整合性", mismatch == 0,
                         f"不一致件数: {mismatch}"))

    # 20 confinement_hours の合理範囲 (3h ~ 24h)
    ch = pd.to_numeric(df["confinement_hours"], errors="coerce")
    out_of_range = ((ch < 3) | (ch > 24)).sum()
    results.append(check("20 confinement_hoursが合理範囲(3h~24h)", out_of_range == 0,
                         f"範囲外: {out_of_range}"))

    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"\n結果: {passed}/{total} PASS")

    if passed == total:
        print("[SUCCESS] 全チェックPASS")
        sys.exit(0)
    else:
        print(f"[FAIL] {total - passed}項目が失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()

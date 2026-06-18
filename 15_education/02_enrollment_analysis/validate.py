# -*- coding: utf-8 -*-
"""
C-55 生徒入学申込・入学率分析パイプライン
クレンジング後データのバリデーション（18項目チェック）
"""

import os
import sys
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CLEANED_FILE = os.path.join(OUTPUT_DIR, "cleaned_applications_202401.csv")

# optional列（欠損率チェックから除外）
OPTIONAL_COLS = ["decline_reason"]

REQUIRED_COLS = [
    "app_date", "app_id", "department", "selection_method", "region",
    "result", "score", "interview_flag", "decline_reason",
    "is_enrolled", "score_grade", "source_file"
]

EXPECTED_DEPARTMENTS = {"文系", "理系", "芸術系", "体育系"}
EXPECTED_SELECTION_METHODS = {"一般", "推薦", "AO"}
EXPECTED_REGIONS = {"東京", "大阪", "名古屋", "福岡", "仙台"}
EXPECTED_SOURCE_FILES = {
    "applications_styleA.csv",
    "applications_styleB.csv",
    "applications_styleC.csv"
}


def check(label, condition):
    status = "[PASS]" if condition else "[FAIL]"
    print(f"{status} {label}")
    return condition


def main():
    results = []

    # 1. ファイル存在チェック
    file_exists = os.path.exists(CLEANED_FILE)
    results.append(check("ファイルが存在する", file_exists))

    if not file_exists:
        print(f"\nResult: 1/{len(results)} checks passed")
        sys.exit(1)

    df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")

    # 2. 行数 >= 420
    results.append(check(f"行数が420以上 (実際: {len(df)})", len(df) >= 420))

    # 3. 必須列が存在する
    missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
    results.append(check(f"必須列がすべて存在する (不足: {missing_cols})", len(missing_cols) == 0))

    # 4. app_date フォーマット YYYY-MM-DD
    date_valid = df["app_date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$").all()
    results.append(check("app_date が YYYY-MM-DD 形式", bool(date_valid)))

    # 5. app_id 一意性
    results.append(check("app_id に重複がない", df["app_id"].nunique() == len(df)))

    # 6. department 4種類
    depts = set(df["department"].dropna().unique())
    results.append(check(f"department が4種類 (実際: {depts})", depts == EXPECTED_DEPARTMENTS))

    # 7. selection_method 3種類
    sels = set(df["selection_method"].dropna().unique())
    results.append(check(f"selection_method が3種類 (実際: {sels})", sels == EXPECTED_SELECTION_METHODS))

    # 8. region 5種類
    regs = set(df["region"].dropna().unique())
    results.append(check(f"region が5種類 (実際: {regs})", regs == EXPECTED_REGIONS))

    # 9. score が [50, 100] の範囲
    score_valid = df["score"].dropna().between(50, 100).all()
    results.append(check("score が [50, 100] の範囲内", bool(score_valid)))

    # 10. interview_flag が 0 または 1 のみ
    iflags = set(df["interview_flag"].dropna().astype(int).unique())
    results.append(check(f"interview_flag が 0/1 のみ (実際: {iflags})", iflags.issubset({0, 1})))

    # 11. is_enrolled が 0 または 1 のみ
    enrolls = set(df["is_enrolled"].dropna().astype(int).unique())
    results.append(check(f"is_enrolled が 0/1 のみ (実際: {enrolls})", enrolls.issubset({0, 1})))

    # 12. score_grade 3種類
    grades = set(df["score_grade"].dropna().unique())
    expected_grades = {"高得点", "中得点", "低得点"}
    results.append(check(f"score_grade が3種類 (実際: {grades})", grades == expected_grades))

    # 13. 欠損率 <= 15%（optional列除く）
    check_cols = [c for c in REQUIRED_COLS if c not in OPTIONAL_COLS and c in df.columns]
    max_null_rate = 0.0
    worst_col = ""
    for col in check_cols:
        rate = df[col].isnull().mean()
        if rate > max_null_rate:
            max_null_rate = rate
            worst_col = col
    results.append(check(
        f"欠損率が15%以下 (最大: {worst_col}={max_null_rate:.1%})",
        max_null_rate <= 0.15
    ))

    # 14. source_file が3種類
    srcs = set(df["source_file"].dropna().unique())
    results.append(check(f"source_file が3種類 (実際: {srcs})", srcs == EXPECTED_SOURCE_FILES))

    # 15. 合格件数 >= 1
    pass_count = (df["result"] == "合格").sum()
    results.append(check(f"合格件数が1以上 (実際: {pass_count})", pass_count >= 1))

    # 16. 不合格件数 >= 1
    fail_count = (df["result"] == "不合格").sum()
    results.append(check(f"不合格件数が1以上 (実際: {fail_count})", fail_count >= 1))

    # 17. 面接あり件数 >= 1
    interview_count = (df["interview_flag"] == 1).sum()
    results.append(check(f"面接あり件数が1以上 (実際: {interview_count})", interview_count >= 1))

    # 18. result が 合格/不合格 のみ
    results_vals = set(df["result"].dropna().unique())
    results.append(check(
        f"result が合格/不合格のみ (実際: {results_vals})",
        results_vals.issubset({"合格", "不合格"})
    ))

    total = len(results)
    passed = sum(results)
    print(f"\nResult: {passed}/{total} checks passed")

    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()

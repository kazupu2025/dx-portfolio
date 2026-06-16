"""
validate.py
cleaned_shift_202401.csv の品質を18項目チェックする。
全PASS しなければ exit(1) で終了する。
"""

import os
import sys
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "output", "cleaned_shift_202401.csv")

VALID_SHIFTS = {"早番", "日勤", "遅番", "夜勤", "休み"}
VALID_SKILLS = {"初級", "中級", "上級"}
VALID_EMPLOYMENTS = {"正社員", "パート", "派遣"}
VALID_ROLES = {"看護師", "介護士", "看護補助", "リハビリ師"}


def run_checks():
    results = []

    def chk(name: str, passed: bool, detail: str = ""):
        status = "PASS" if passed else "FAIL"
        msg = f"[{status}] {name}"
        if detail:
            msg += f"  ({detail})"
        print(msg)
        results.append((name, passed))

    # ── 1. ファイルの存在 ───────────────────────────────────────────────
    chk("CSVファイルが存在する", os.path.isfile(OUTPUT_FILE), OUTPUT_FILE)

    if not os.path.isfile(OUTPUT_FILE):
        print("\n[NG] ファイルが存在しないため残りのチェックをスキップします")
        return results

    df = pd.read_csv(OUTPUT_FILE, encoding="utf-8-sig")

    # ── 2. 行数（450行以上） ────────────────────────────────────────────
    chk("行数が450以上", len(df) >= 450, f"{len(df)}行")

    # ── 3〜9. 必須列の存在 ─────────────────────────────────────────────
    required_cols = [
        "staff_id", "name", "role", "date",
        "preferred_shift", "skill_level", "employment_type"
    ]
    for col in required_cols:
        chk(f"列 '{col}' が存在する", col in df.columns)

    # ── 10. source_file 列の存在 ────────────────────────────────────────
    chk("列 'source_file' が存在する", "source_file" in df.columns)

    # ── 11. is_night 列の存在と bool 型 ───────────────────────────────
    chk("列 'is_night' が存在する", "is_night" in df.columns)
    if "is_night" in df.columns:
        chk(
            "is_night が bool 型（True/False のみ）",
            df["is_night"].dropna().isin([True, False]).all(),
            str(df["is_night"].unique()[:5].tolist()),
        )

    # ── 12. is_off 列の存在と bool 型 ─────────────────────────────────
    chk("列 'is_off' が存在する", "is_off" in df.columns)
    if "is_off" in df.columns:
        chk(
            "is_off が bool 型（True/False のみ）",
            df["is_off"].dropna().isin([True, False]).all(),
            str(df["is_off"].unique()[:5].tolist()),
        )

    # ── 13. 日付フォーマット（YYYY-MM-DD） ────────────────────────────
    if "date" in df.columns:
        import re
        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        bad_dates = df["date"].dropna().apply(lambda v: not bool(date_pattern.match(str(v))))
        chk("日付が YYYY-MM-DD 形式", not bad_dates.any(), f"不正: {bad_dates.sum()}件")

    # ── 14. preferred_shift の値域 ────────────────────────────────────
    if "preferred_shift" in df.columns:
        invalid_shifts = df["preferred_shift"].dropna()[~df["preferred_shift"].dropna().isin(VALID_SHIFTS)]
        chk(
            "preferred_shift が定義値のみ",
            len(invalid_shifts) == 0,
            f"不正値: {invalid_shifts.unique().tolist()[:5]}",
        )

    # ── 15. skill_level の値域 ────────────────────────────────────────
    if "skill_level" in df.columns:
        invalid_skills = df["skill_level"].dropna()[~df["skill_level"].dropna().isin(VALID_SKILLS)]
        chk(
            "skill_level が定義値のみ",
            len(invalid_skills) == 0,
            f"不正値: {invalid_skills.unique().tolist()[:5]}",
        )

    # ── 16. employment_type の値域 ────────────────────────────────────
    if "employment_type" in df.columns:
        invalid_emp = df["employment_type"].dropna()[
            ~df["employment_type"].dropna().isin(VALID_EMPLOYMENTS)
        ]
        chk(
            "employment_type が定義値のみ",
            len(invalid_emp) == 0,
            f"不正値: {invalid_emp.unique().tolist()[:5]}",
        )

    # ── 17. role の値域 ───────────────────────────────────────────────
    if "role" in df.columns:
        invalid_roles = df["role"].dropna()[~df["role"].dropna().isin(VALID_ROLES)]
        chk(
            "role が定義値のみ",
            len(invalid_roles) == 0,
            f"不正値: {invalid_roles.unique().tolist()[:5]}",
        )

    # ── 18. staff_id のユニーク数（20以上） ───────────────────────────
    if "staff_id" in df.columns:
        n_staff = df["staff_id"].nunique()
        chk("staff_id のユニーク数が20以上", n_staff >= 20, f"{n_staff}名")

    # ── 19. 欠損率15%以下 ─────────────────────────────────────────────
    miss_rate = df.isnull().mean().max()
    chk("欠損率が15%以下", miss_rate <= 0.15, f"最大欠損率: {miss_rate:.1%}")

    # ── 20. 夜勤比率が5%以上30%以下 ──────────────────────────────────
    if "preferred_shift" in df.columns:
        night_ratio = (df["preferred_shift"] == "夜勤").mean()
        chk(
            "夜勤比率が5%以上30%以下",
            0.05 <= night_ratio <= 0.30,
            f"{night_ratio:.1%}",
        )

    # ── 21. 日付が 2024-01 内 ─────────────────────────────────────────
    if "date" in df.columns:
        out_of_range = df["date"].dropna().apply(
            lambda v: not str(v).startswith("2024-01")
        )
        chk("日付が 2024-01 内", not out_of_range.any(), f"範囲外: {out_of_range.sum()}件")

    # ── 22. (staff_id, date) の重複なし ──────────────────────────────
    if "staff_id" in df.columns and "date" in df.columns:
        dup = df.duplicated(subset=["staff_id", "date"]).sum()
        chk("(staff_id, date) の重複なし", dup == 0, f"重複: {dup}件")

    return results


def main():
    print("=" * 50)
    print("validate.py - クレンジング品質チェック")
    print("=" * 50)

    results = run_checks()

    passed = sum(1 for _, ok in results if ok)
    failed = sum(1 for _, ok in results if not ok)
    total = len(results)

    print()
    print(f"結果: {passed}/{total} PASS  /  {failed} FAIL")

    if failed > 0:
        print("\n[NG] FAILがあります。cleanse.py を修正して再実行してください。")
        sys.exit(1)
    else:
        print("\n[OK] 全チェック PASS")


if __name__ == "__main__":
    main()

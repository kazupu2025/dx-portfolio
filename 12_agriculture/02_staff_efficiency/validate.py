# -*- coding: utf-8 -*-
"""
C-59 農場スタッフ勤怠・作業効率分析パイプライン
クレンジング出力バリデーション (18チェック)
"""

import os
import sys
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
CLEANED_FILE = os.path.join(BASE_DIR, "output", "cleaned_farm_work_202401.csv")

REQUIRED_COLS = [
    "work_date", "record_id", "staff_id", "work_type", "crop",
    "work_hours", "target_qty", "actual_qty", "is_target_met",
    "achievement_rate", "productivity", "efficiency_grade", "source_file",
]

EXPECTED_WORK_TYPES = {"播種", "施肥", "収穫", "管理作業"}
EXPECTED_CROPS = {"トマト", "キュウリ", "レタス", "イチゴ", "ホウレンソウ"}
EXPECTED_GRADES = {"高効率", "中効率", "低効率"}
EXPECTED_SOURCES = {"farm_work_styleA.csv", "farm_work_styleB.csv", "farm_work_styleC.csv"}

results = []


def check(name, passed, detail=""):
    label = "[PASS]" if passed else "[FAIL]"
    msg = f"{label} {name}"
    if detail:
        msg += f" | {detail}"
    print(msg)
    results.append(passed)


def main():
    # 1. ファイル存在
    check("ファイル存在", os.path.exists(CLEANED_FILE), CLEANED_FILE)
    if not os.path.exists(CLEANED_FILE):
        print("Result: 0/18 checks passed")
        sys.exit(1)

    df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")

    # 2. 行数 >= 420
    check("行数>=420", len(df) >= 420, f"rows={len(df)}")

    # 3. 必須列の存在
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    check("必須列の存在", len(missing) == 0, f"missing={missing}")

    # 4. work_dateフォーマット YYYY-MM-DD
    try:
        parsed = pd.to_datetime(df["work_date"], format="%Y-%m-%d", errors="coerce")
        bad = parsed.isna().sum()
        check("work_dateフォーマット", bad == 0, f"bad_count={bad}")
    except Exception as e:
        check("work_dateフォーマット", False, str(e))

    # 5. record_id 一意性
    dups = df["record_id"].duplicated().sum()
    check("record_id一意性", dups == 0, f"duplicates={dups}")

    # 6. staff_id 種類 >= 5
    staff_count = df["staff_id"].nunique()
    check("staff_id種類>=5", staff_count >= 5, f"count={staff_count}")

    # 7. work_type 4種類
    work_types = set(df["work_type"].dropna().unique())
    check("work_type 4種類", work_types == EXPECTED_WORK_TYPES, f"found={work_types}")

    # 8. crop 5種類
    crops = set(df["crop"].dropna().unique())
    check("crop 5種類", crops == EXPECTED_CROPS, f"found={crops}")

    # 9. work_hours > 0
    bad_hours = (df["work_hours"] <= 0).sum()
    check("work_hours>0", bad_hours == 0, f"bad_count={bad_hours}")

    # 10. target_qty > 0
    bad_target = (df["target_qty"] <= 0).sum()
    check("target_qty>0", bad_target == 0, f"bad_count={bad_target}")

    # 11. actual_qty >= 0
    bad_actual = (df["actual_qty"] < 0).sum()
    check("actual_qty>=0", bad_actual == 0, f"bad_count={bad_actual}")

    # 12. is_target_met 0/1のみ
    invalid_met = (~df["is_target_met"].isin([0, 1])).sum()
    check("is_target_met 0/1のみ", invalid_met == 0, f"invalid_count={invalid_met}")

    # 13. achievement_rate >= 0
    ar = df["achievement_rate"].dropna()
    bad_ar = (ar < 0).sum()
    check("achievement_rate>=0", bad_ar == 0, f"bad_count={bad_ar}")

    # 14. productivity >= 0
    prod = df["productivity"].dropna()
    bad_prod = (prod < 0).sum()
    check("productivity>=0", bad_prod == 0, f"bad_count={bad_prod}")

    # 15. efficiency_grade 3種類
    grades = set(df["efficiency_grade"].dropna().unique())
    check("efficiency_grade 3種類", grades == EXPECTED_GRADES, f"found={grades}")

    # 16. 欠損率 <= 15%
    null_rate = df.isnull().mean().max()
    check("欠損率<=15%", null_rate <= 0.15, f"max_null_rate={null_rate:.2%}")

    # 17. source_file 3種類
    sources = set(df["source_file"].dropna().unique())
    check("source_file 3種類", sources == EXPECTED_SOURCES, f"found={sources}")

    # 18. 目標達成件数 >= 1
    met_count = (df["is_target_met"] == 1).sum()
    check("目標達成件数>=1", met_count >= 1, f"count={met_count}")

    passed = sum(results)
    total = len(results)
    print(f"Result: {passed}/{total} checks passed")
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
C-49 作物収量・品質検査レポートパイプライン
クレンジング出力バリデーション (18チェック)
"""

import os
import sys
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
CLEANED_FILE = os.path.join(BASE_DIR, "output", "cleaned_harvest_202401.csv")

REQUIRED_COLS = [
    "harvest_date", "record_id", "farm_id", "farm_name",
    "crop", "harvest_qty", "grade_a_qty", "defect_qty",
    "inspector_id", "grade_a_rate", "defect_rate", "quality_flag", "source_file",
]

EXPECTED_FARMS = {"農場A", "農場B", "農場C", "農場D"}
EXPECTED_CROPS = {"トマト", "キュウリ", "ピーマン", "レタス", "ほうれん草"}
EXPECTED_FLAGS = {"優良", "合格", "要改善"}
EXPECTED_SOURCES = {"harvest_styleA.csv", "harvest_styleB.csv", "harvest_styleC.csv"}

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

    # 4. harvest_dateフォーマット YYYY-MM-DD
    try:
        parsed = pd.to_datetime(df["harvest_date"], format="%Y-%m-%d", errors="coerce")
        bad = parsed.isna().sum()
        check("harvest_dateフォーマット", bad == 0, f"bad_count={bad}")
    except Exception as e:
        check("harvest_dateフォーマット", False, str(e))

    # 5. record_id 一意性
    dups = df["record_id"].duplicated().sum()
    check("record_id一意性", dups == 0, f"duplicates={dups}")

    # 6. farm_name 4種類
    farms = set(df["farm_name"].dropna().unique())
    check("farm_name 4種類", farms == EXPECTED_FARMS, f"found={farms}")

    # 7. crop 5種類
    crops = set(df["crop"].dropna().unique())
    check("crop 5種類", crops == EXPECTED_CROPS, f"found={crops}")

    # 8. harvest_qty > 0
    bad_qty = (df["harvest_qty"] <= 0).sum()
    check("harvest_qty>0", bad_qty == 0, f"bad_count={bad_qty}")

    # 9. grade_a_qty >= 0
    bad_grade = (df["grade_a_qty"] < 0).sum()
    check("grade_a_qty>=0", bad_grade == 0, f"bad_count={bad_grade}")

    # 10. defect_qty >= 0
    bad_defect = (df["defect_qty"] < 0).sum()
    check("defect_qty>=0", bad_defect == 0, f"bad_count={bad_defect}")

    # 11. grade_a_rate in [0,1]
    r = df["grade_a_rate"].dropna()
    bad_rate = ((r < 0) | (r > 1)).sum()
    check("grade_a_rate in [0,1]", bad_rate == 0, f"bad_count={bad_rate}")

    # 12. defect_rate in [0,1]
    dr = df["defect_rate"].dropna()
    bad_dr = ((dr < 0) | (dr > 1)).sum()
    check("defect_rate in [0,1]", bad_dr == 0, f"bad_count={bad_dr}")

    # 13. quality_flag 3種類
    flags = set(df["quality_flag"].dropna().unique())
    check("quality_flag 3種類", flags == EXPECTED_FLAGS, f"found={flags}")

    # 14. 欠損率 <= 15%
    null_rate = df.isnull().mean().max()
    check("欠損率<=15%", null_rate <= 0.15, f"max_null_rate={null_rate:.2%}")

    # 15. source_file 3種類
    sources = set(df["source_file"].dropna().unique())
    check("source_file 3種類", sources == EXPECTED_SOURCES, f"found={sources}")

    # 16. 優良件数 >= 1
    yuryo = (df["quality_flag"] == "優良").sum()
    check("優良件数>=1", yuryo >= 1, f"count={yuryo}")

    # 17. 要改善件数 >= 1
    kaizen = (df["quality_flag"] == "要改善").sum()
    check("要改善件数>=1", kaizen >= 1, f"count={kaizen}")

    # 18. inspector_id 種類 >= 3
    insp_count = df["inspector_id"].nunique()
    check("inspector_id種類>=3", insp_count >= 3, f"count={insp_count}")

    passed = sum(results)
    total = len(results)
    print(f"Result: {passed}/{total} checks passed")
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()

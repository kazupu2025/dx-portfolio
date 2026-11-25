# -*- coding: utf-8 -*-
"""
C-59 農場スタッフ勤怠・作業効率分析パイプライン
レポート出力バリデーション (10チェック)
"""

import os
import sys
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
REPORT_FILE = os.path.join(BASE_DIR, "output", "analysis_report.md")
CROP_CSV = os.path.join(BASE_DIR, "output", "crop_summary_202401.csv")

results = []


def check(name, passed, detail=""):
    label = "[PASS]" if passed else "[FAIL]"
    msg = f"{label} {name}"
    if detail:
        msg += f" | {detail}"
    print(msg)
    results.append(passed)


def main():
    # 1. analysis_report.md 存在
    check("analysis_report.md 存在", os.path.exists(REPORT_FILE))

    # 2. crop_summary_202401.csv 存在
    check("crop_summary_202401.csv 存在", os.path.exists(CROP_CSV))

    if not os.path.exists(REPORT_FILE):
        print("Result: 0/10 checks passed")
        sys.exit(1)

    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 3. レポートに作物名が含まれる
    crops_ok = all(crop in content for crop in ["トマト", "キュウリ", "レタス", "イチゴ", "ホウレンソウ"])
    check("レポートに作物名5種", crops_ok)

    # 4. レポートに作業区分が含まれる
    wt_ok = all(wt in content for wt in ["播種", "施肥", "収穫", "管理作業"])
    check("レポートに作業区分4種", wt_ok)

    # 5. レポートにスタッフIDが含まれる
    staff_ok = any(f"STAFF-{i:02d}" in content for i in range(1, 11))
    check("レポートにスタッフID", staff_ok)

    # 6. レポートに効率グレードが含まれる
    grade_ok = all(g in content for g in ["高効率", "中効率", "低効率"])
    check("レポートに効率グレード3種", grade_ok)

    # 7. crop_summary CSVの列チェック
    if os.path.exists(CROP_CSV):
        df = pd.read_csv(CROP_CSV, encoding="utf-8-sig")
        required_cols = ["crop", "achievement_rate_mean", "productivity_mean", "work_hours_sum", "record_count"]
        missing = [c for c in required_cols if c not in df.columns]
        check("crop_summary 必須列", len(missing) == 0, f"missing={missing}")

        # 8. crop_summary 5行
        check("crop_summary 5行", len(df) == 5, f"rows={len(df)}")

        # 9. productivity_mean > 0 全行
        all_pos = (df["productivity_mean"] > 0).all()
        check("productivity_mean>0 全行", bool(all_pos))
    else:
        check("crop_summary 必須列", False, "file missing")
        check("crop_summary 5行", False, "file missing")
        check("productivity_mean>0 全行", False, "file missing")

    # 10. レポートに総記録数の記載
    check("レポートに総記録数記載", "総記録数" in content)

    passed = sum(results)
    total = len(results)
    print(f"Result: {passed}/{total} checks passed")
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()

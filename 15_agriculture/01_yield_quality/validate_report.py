# -*- coding: utf-8 -*-
"""
C-49 作物収量・品質検査レポートパイプライン
レポート出力バリデーション (10チェック)
"""

import os
import sys
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
REPORT_FILE = os.path.join(BASE_DIR, "output", "analysis_report.md")
FARM_CSV = os.path.join(BASE_DIR, "output", "farm_summary_202401.csv")

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

    # 2. farm_summary_202401.csv 存在
    check("farm_summary_202401.csv 存在", os.path.exists(FARM_CSV))

    if not os.path.exists(REPORT_FILE):
        print("Result: 0/10 checks passed")
        sys.exit(1)

    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 3. レポートに農場名が含まれる
    farms_ok = all(farm in content for farm in ["農場A", "農場B", "農場C", "農場D"])
    check("レポートに農場名4件", farms_ok)

    # 4. レポートに作物名が含まれる
    crops_ok = all(crop in content for crop in ["トマト", "キュウリ", "ピーマン", "レタス", "ほうれん草"])
    check("レポートに作物名5種", crops_ok)

    # 5. レポートに検査員IDが含まれる
    insp_ok = any(f"INS-0{i}" in content for i in range(1, 6))
    check("レポートに検査員ID", insp_ok)

    # 6. レポートに品質フラグが含まれる
    flag_ok = all(f in content for f in ["優良", "合格", "要改善"])
    check("レポートに品質フラグ3種", flag_ok)

    # 7. farm_summary CSVの列チェック
    if os.path.exists(FARM_CSV):
        df = pd.read_csv(FARM_CSV, encoding="utf-8-sig")
        required_cols = ["farm_name", "total_harvest", "mean_grade_a_rate", "mean_defect_rate", "record_count"]
        missing = [c for c in required_cols if c not in df.columns]
        check("farm_summary 必須列", len(missing) == 0, f"missing={missing}")

        # 8. farm_summary 4行
        check("farm_summary 4行", len(df) == 4, f"rows={len(df)}")

        # 9. total_harvest > 0 全行
        all_pos = (df["total_harvest"] > 0).all()
        check("total_harvest>0 全行", bool(all_pos))
    else:
        check("farm_summary 必須列", False, "file missing")
        check("farm_summary 4行", False, "file missing")
        check("total_harvest>0 全行", False, "file missing")

    # 10. レポートに総レコード数の記載
    check("レポートに総レコード数記載", "総レコード数" in content)

    passed = sum(results)
    total = len(results)
    print(f"Result: {passed}/{total} checks passed")
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()

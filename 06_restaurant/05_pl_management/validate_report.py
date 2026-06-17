# -*- coding: utf-8 -*-
"""
C-54: 店舗別損益・原価率管理パイプライン
分析レポートバリデーションスクリプト（10項目チェック）
"""

import pandas as pd
from pathlib import Path
import sys

OUTPUT_DIR = Path(__file__).parent / "output"
REPORT_FILE = OUTPUT_DIR / "analysis_report.md"
SUMMARY_FILE = OUTPUT_DIR / "store_pl_summary_202401.csv"


def check(label: str, result: bool, detail: str = "") -> bool:
    status = "[PASS]" if result else "[FAIL]"
    msg = f"{status} {label}"
    if detail:
        msg += f" | {detail}"
    print(msg)
    return result


def validate() -> bool:
    results = []

    # 1. analysis_report.md 存在確認
    results.append(check("analysis_report.md 存在確認", REPORT_FILE.exists(), str(REPORT_FILE)))

    # 2. store_pl_summary_202401.csv 存在確認
    results.append(check("store_pl_summary_202401.csv 存在確認", SUMMARY_FILE.exists(), str(SUMMARY_FILE)))

    if not REPORT_FILE.exists() or not SUMMARY_FILE.exists():
        print("[ERROR] ファイルが存在しないため残りのチェックをスキップします")
        return False

    # 3. レポートにタイトルが含まれる
    report_text = REPORT_FILE.read_text(encoding="utf-8")
    results.append(check("レポートにタイトルが含まれる", "店舗別損益" in report_text))

    # 4. レポートに店舗名が含まれる
    stores = ["渋谷店", "新宿店", "池袋店", "銀座店", "品川店"]
    stores_in_report = all(s in report_text for s in stores)
    results.append(check("レポートに5店舗が含まれる", stores_in_report,
                          f"含まれない店舗: {[s for s in stores if s not in report_text]}"))

    # 5. レポートに黒字/赤字が含まれる
    has_pl_flag = "黒字" in report_text or "赤字" in report_text
    results.append(check("レポートに損益フラグが含まれる", has_pl_flag))

    # 6. サマリーCSV 行数 == 5（5店舗）
    df_sum = pd.read_csv(SUMMARY_FILE, encoding="utf-8-sig")
    results.append(check("サマリーCSV 行数 == 5", len(df_sum) == 5,
                          f"実際: {len(df_sum)} 行"))

    # 7. サマリーCSVに必須列が含まれる
    required_sum_cols = ["store_name", "total_revenue", "total_gross_profit", "pl_status"]
    missing_sum = [c for c in required_sum_cols if c not in df_sum.columns]
    results.append(check("サマリーCSV 必須列の存在", len(missing_sum) == 0,
                          f"不足列: {missing_sum}"))

    # 8. total_revenue が全て正の値
    if "total_revenue" in df_sum.columns:
        rev_pos = (pd.to_numeric(df_sum["total_revenue"], errors="coerce") > 0).all()
        results.append(check("total_revenue > 0", rev_pos))
    else:
        results.append(check("total_revenue > 0", False, "列が存在しない"))

    # 9. pl_status が 黒字/赤字 のみ
    if "pl_status" in df_sum.columns:
        pl_vals = set(df_sum["pl_status"].unique())
        pl_ok = pl_vals.issubset({"黒字", "赤字"})
        results.append(check("pl_status が 黒字/赤字 のみ", pl_ok,
                              f"実際: {sorted(pl_vals)}"))
    else:
        results.append(check("pl_status が 黒字/赤字 のみ", False, "列が存在しない"))

    # 10. レポートに売上トレンドセクションが含まれる
    results.append(check("レポートに日別売上トレンドが含まれる", "日別売上トレンド" in report_text))

    passed = sum(results)
    total = len(results)
    print(f"\nResult: {passed}/{total} checks passed")
    return passed == total


def main():
    print("=" * 60)
    print("Report Validation (10 checks)")
    print("=" * 60)
    success = validate()
    print("=" * 60)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
C-54: 店舗別損益・原価率管理パイプライン
クレンジング出力バリデーションスクリプト（18項目チェック）
"""

import pandas as pd
from pathlib import Path
import sys

OUTPUT_DIR = Path(__file__).parent / "output"
TARGET_FILE = OUTPUT_DIR / "cleaned_pl_202401.csv"

REQUIRED_COLS = [
    "record_date", "record_id", "store_name", "revenue",
    "food_cost", "labor_cost", "other_cost",
    "total_cost", "gross_profit",
    "food_cost_rate", "labor_cost_rate", "profit_margin",
    "pl_flag", "source_file",
]

STORES_EXPECTED = {"渋谷店", "新宿店", "池袋店", "銀座店", "品川店"}


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
    date_pattern = df["record_date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")
    results.append(check("日付フォーマット YYYY-MM-DD", date_pattern.all(),
                          f"不正行数: {(~date_pattern).sum()}"))

    # 5. record_id 一意性
    id_unique = df["record_id"].nunique() == len(df)
    results.append(check("record_id 一意性", id_unique,
                          f"重複数: {len(df) - df['record_id'].nunique()}"))

    # 6. store_name が5種類
    store_count = df["store_name"].nunique()
    results.append(check("store_name が 5 種類", store_count == 5,
                          f"実際: {store_count} 種類 {df['store_name'].unique().tolist()}"))

    # 7. revenue > 0
    rev_vals = pd.to_numeric(df["revenue"], errors="coerce")
    rev_positive = (rev_vals > 0).all()
    results.append(check("revenue > 0", rev_positive,
                          f"最小値: {rev_vals.min()}"))

    # 8. food_cost >= 0
    fc_vals = pd.to_numeric(df["food_cost"], errors="coerce")
    fc_valid = (fc_vals >= 0).all()
    results.append(check("food_cost >= 0", fc_valid,
                          f"最小値: {fc_vals.min()}"))

    # 9. labor_cost >= 0
    lc_vals = pd.to_numeric(df["labor_cost"], errors="coerce")
    lc_valid = (lc_vals >= 0).all()
    results.append(check("labor_cost >= 0", lc_valid,
                          f"最小値: {lc_vals.min()}"))

    # 10. other_cost >= 0
    oc_vals = pd.to_numeric(df["other_cost"], errors="coerce")
    oc_valid = (oc_vals >= 0).all()
    results.append(check("other_cost >= 0", oc_valid,
                          f"最小値: {oc_vals.min()}"))

    # 11. total_cost > 0
    tc_vals = pd.to_numeric(df["total_cost"], errors="coerce")
    tc_positive = (tc_vals > 0).all()
    results.append(check("total_cost > 0", tc_positive,
                          f"最小値: {tc_vals.min()}"))

    # 12. gross_profit 計算整合性 (revenue - total_cost)
    rev = pd.to_numeric(df["revenue"], errors="coerce")
    tc = pd.to_numeric(df["total_cost"], errors="coerce")
    gp = pd.to_numeric(df["gross_profit"], errors="coerce")
    gp_diff = (gp - (rev - tc)).abs()
    gp_ok = (gp_diff < 1).all()
    results.append(check("gross_profit 計算整合性 (revenue-total_cost)", gp_ok,
                          f"最大誤差: {gp_diff.max():.4f}"))

    # 13. food_cost_rate in [0, 1]
    fcr_vals = pd.to_numeric(df["food_cost_rate"], errors="coerce").dropna()
    fcr_ok = ((fcr_vals >= 0) & (fcr_vals <= 1)).all()
    results.append(check("food_cost_rate in [0, 1]", fcr_ok,
                          f"範囲外: {((fcr_vals < 0) | (fcr_vals > 1)).sum()} 件"))

    # 14. labor_cost_rate in [0, 1]
    lcr_vals = pd.to_numeric(df["labor_cost_rate"], errors="coerce").dropna()
    lcr_ok = ((lcr_vals >= 0) & (lcr_vals <= 1)).all()
    results.append(check("labor_cost_rate in [0, 1]", lcr_ok,
                          f"範囲外: {((lcr_vals < 0) | (lcr_vals > 1)).sum()} 件"))

    # 15. profit_margin in [-1, 1]
    pm_vals = pd.to_numeric(df["profit_margin"], errors="coerce").dropna()
    pm_ok = ((pm_vals >= -1) & (pm_vals <= 1)).all()
    results.append(check("profit_margin in [-1, 1]", pm_ok,
                          f"範囲外: {((pm_vals < -1) | (pm_vals > 1)).sum()} 件"))

    # 16. pl_flag の種類 == 2（黒字/赤字）
    flag_vals = set(df["pl_flag"].unique())
    flag_ok = flag_vals.issubset({"黒字", "赤字"}) and len(flag_vals) == 2
    results.append(check("pl_flag 種類 == 2 (黒字/赤字)", flag_ok,
                          f"実際: {sorted(flag_vals)}"))

    # 17. 欠損率 <= 15%
    total_cells = df.shape[0] * df.shape[1]
    null_cells = df.isnull().sum().sum()
    null_rate = null_cells / total_cells if total_cells > 0 else 0
    results.append(check("欠損率 <= 15%", null_rate <= 0.15,
                          f"欠損率: {null_rate:.2%}"))

    # 18. source_file が 3 種類
    src_count = df["source_file"].nunique()
    results.append(check("source_file が 3 種類", src_count == 3,
                          f"実際: {src_count} 種類"))

    passed = sum(results)
    total = len(results)
    print(f"\nResult: {passed}/{total} checks passed")
    return passed == total


def main():
    print("=" * 60)
    print("Cleansing Output Validation (18 checks)")
    print("=" * 60)
    success = validate()
    print("=" * 60)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

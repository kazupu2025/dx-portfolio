# -*- coding: utf-8 -*-
"""
C-29: 薬品在庫管理・発注アラートパイプライン
バリデーションスクリプト: cleaned CSV の品質を 18 項目以上チェックする
絵文字・em-dash・記号は使わず [PASS]/[FAIL] で出力する
"""

import pandas as pd
import numpy as np
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CSV_PATH = OUTPUT_DIR / "cleaned_medicine_202401.csv"

REQUIRED_COLS = ["date", "med_code", "med_name", "category", "ward",
                 "stock_qty", "min_stock", "daily_usage", "unit_price",
                 "source_file", "days_until_stockout", "stock_value", "alert_level"]


def run_checks(df: pd.DataFrame) -> list[tuple[str, bool, str]]:
    """チェック結果を (チェック名, 合否, 詳細メッセージ) のリストで返す"""
    results = []

    def ok(name, detail=""):
        results.append((name, True, detail))

    def ng(name, detail=""):
        results.append((name, False, detail))

    # 1. 行数 >= 400
    if len(df) >= 400:
        ok("行数 >= 400", f"{len(df)} 件")
    else:
        ng("行数 >= 400", f"{len(df)} 件 (期待: >= 400)")

    # 2. 必須列の存在
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if not missing:
        ok("必須列の存在", f"{len(REQUIRED_COLS)} 列すべて存在")
    else:
        ng("必須列の存在", f"不足列: {missing}")

    # 3. 日付フォーマット YYYY-MM-DD
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    bad_dates = df["date"].dropna()[~df["date"].dropna().apply(lambda x: bool(date_pattern.match(str(x))))]
    if len(bad_dates) == 0:
        ok("日付フォーマット YYYY-MM-DD", "全行一致")
    else:
        ng("日付フォーマット YYYY-MM-DD", f"{len(bad_dates)} 件不正")

    # 4. med_code が 30 種類以上
    n_codes = df["med_code"].nunique()
    if n_codes >= 30:
        ok("med_code 30 種類以上", f"{n_codes} 種類")
    else:
        ng("med_code 30 種類以上", f"{n_codes} 種類 (期待: >= 30)")

    # 5. category が 5 種類
    n_cat = df["category"].nunique()
    if n_cat == 5:
        ok("category が 5 種類", f"{sorted(df['category'].unique())}")
    else:
        ng("category が 5 種類", f"{n_cat} 種類: {sorted(df['category'].unique())}")

    # 6. ward が 4 種類
    n_ward = df["ward"].nunique()
    if n_ward == 4:
        ok("ward が 4 種類", f"{sorted(df['ward'].unique())}")
    else:
        ng("ward が 4 種類", f"{n_ward} 種類")

    # 7. stock_qty >= 0
    bad_sq = df["stock_qty"].dropna()[df["stock_qty"].dropna() < 0]
    if len(bad_sq) == 0:
        ok("stock_qty >= 0", "全行非負")
    else:
        ng("stock_qty >= 0", f"{len(bad_sq)} 件が負値")

    # 8. min_stock > 0
    bad_ms = df["min_stock"].dropna()[df["min_stock"].dropna() <= 0]
    if len(bad_ms) == 0:
        ok("min_stock > 0", "全行正値")
    else:
        ng("min_stock > 0", f"{len(bad_ms)} 件が 0 以下")

    # 9. daily_usage > 0
    bad_du = df["daily_usage"].dropna()[df["daily_usage"].dropna() <= 0]
    if len(bad_du) == 0:
        ok("daily_usage > 0", "全行正値")
    else:
        ng("daily_usage > 0", f"{len(bad_du)} 件が 0 以下")

    # 10. unit_price > 0
    bad_up = df["unit_price"].dropna()[df["unit_price"].dropna() <= 0]
    if len(bad_up) == 0:
        ok("unit_price > 0", "全行正値")
    else:
        ng("unit_price > 0", f"{len(bad_up)} 件が 0 以下")

    # 11. days_until_stockout が非負 (またはNaN)
    ds = df["days_until_stockout"].dropna()
    bad_ds = ds[ds < 0]
    if len(bad_ds) == 0:
        ok("days_until_stockout >= 0 or NaN", f"NaN: {df['days_until_stockout'].isna().sum()} 件")
    else:
        ng("days_until_stockout >= 0 or NaN", f"{len(bad_ds)} 件が負値")

    # 12. alert_level が欠品/警告/正常 のみ
    valid_alerts = {"欠品", "警告", "正常"}
    bad_al = df["alert_level"].dropna()[~df["alert_level"].dropna().isin(valid_alerts)]
    if len(bad_al) == 0:
        ok("alert_level 値域", f"有効値のみ: {sorted(df['alert_level'].unique())}")
    else:
        ng("alert_level 値域", f"{len(bad_al)} 件が不正値")

    # 13. 欠品件数 >= 1
    n_shortage = (df["alert_level"] == "欠品").sum()
    if n_shortage >= 1:
        ok("欠品件数 >= 1", f"{n_shortage} 件")
    else:
        ng("欠品件数 >= 1", "欠品レコードが 0 件")

    # 14. source_file 列の存在
    if "source_file" in df.columns:
        ok("source_file 列の存在", "存在する")
    else:
        ng("source_file 列の存在", "列がない")

    # 15. 欠損率 <= 15%
    total_cells = df.shape[0] * df.shape[1]
    null_cells = df.isnull().sum().sum()
    null_rate = null_cells / total_cells if total_cells > 0 else 0
    if null_rate <= 0.15:
        ok("欠損率 <= 15%", f"{null_rate:.1%}")
    else:
        ng("欠損率 <= 15%", f"{null_rate:.1%} (期待: <= 15%)")

    # 16. source_file が 3 種類
    n_src = df["source_file"].nunique() if "source_file" in df.columns else 0
    if n_src == 3:
        ok("source_file が 3 種類", f"{sorted(df['source_file'].unique())}")
    else:
        ng("source_file が 3 種類", f"{n_src} 種類")

    # 17. stock_value が非負
    if "stock_value" in df.columns:
        bad_sv = df["stock_value"].dropna()[df["stock_value"].dropna() < 0]
        if len(bad_sv) == 0:
            ok("stock_value >= 0", "全行非負")
        else:
            ng("stock_value >= 0", f"{len(bad_sv)} 件が負値")
    else:
        ng("stock_value >= 0", "stock_value 列がない")

    # 18. med_name の欠損がない
    na_names = df["med_name"].isna().sum()
    if na_names == 0:
        ok("med_name 欠損なし", "全行非NULL")
    else:
        ng("med_name 欠損なし", f"{na_names} 件が欠損")

    return results


def main():
    print("=" * 60)
    print("バリデーション開始: cleaned_medicine_202401.csv")
    print("=" * 60)

    # CSVファイル存在確認 (チェック1)
    if not CSV_PATH.exists():
        print(f"[FAIL] CSVファイル存在確認: {CSV_PATH} が見つかりません")
        sys.exit(1)
    print(f"[PASS] CSVファイル存在確認: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    results = run_checks(df)

    fail_count = 0
    for name, passed, detail in results:
        tag = "[PASS]" if passed else "[FAIL]"
        suffix = f" -- {detail}" if detail else ""
        print(f"{tag} {name}{suffix}")
        if not passed:
            fail_count += 1

    print("=" * 60)
    total = len(results) + 1  # +1 for file existence check
    print(f"結果: {total - fail_count}/{total} PASS, {fail_count} FAIL")
    if fail_count > 0:
        sys.exit(1)
    print("全チェック PASS")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
C-38: 予約キャンセル集計・傾向分析パイプライン
クレンジング出力バリデーションスクリプト (18項目チェック)
"""

import sys
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_FILE = BASE_DIR / "output" / "cleaned_reservations_202401.csv"

REQUIRED_COLUMNS = [
    "reserv_date", "reserv_no", "store_name", "course",
    "guest_count", "amount", "status", "cancel_reason",
    "is_cancel", "loss_amount", "day_of_week", "source_file",
]

VALID_STATUSES = {"予約済み", "キャンセル", "来店済み"}
VALID_WEEKDAYS = {"月", "火", "水", "木", "金", "土", "日"}


def check(label, condition, detail=""):
    tag = "[PASS]" if condition else "[FAIL]"
    msg = f"{tag} {label}"
    if detail:
        msg += f" -- {detail}"
    print(msg)
    return condition


def main():
    results = []

    # 1. CSVファイル存在確認
    results.append(check("01. CSVファイル存在確認", OUTPUT_FILE.exists(), str(OUTPUT_FILE)))

    if not OUTPUT_FILE.exists():
        print("[FAIL] ファイルが存在しないため以降のチェックをスキップします")
        sys.exit(1)

    df = pd.read_csv(OUTPUT_FILE, encoding="utf-8-sig", dtype=str)

    # 数値列を変換しておく
    df["guest_count_num"] = pd.to_numeric(df.get("guest_count", pd.Series(dtype=str)), errors="coerce")
    df["amount_num"] = pd.to_numeric(df.get("amount", pd.Series(dtype=str)), errors="coerce")
    df["is_cancel_num"] = pd.to_numeric(df.get("is_cancel", pd.Series(dtype=str)), errors="coerce")
    df["loss_amount_num"] = pd.to_numeric(df.get("loss_amount", pd.Series(dtype=str)), errors="coerce")

    # 2. 行数チェック
    results.append(check("02. 行数 >= 420", len(df) >= 420, f"actual={len(df)}"))

    # 3. 必須列の存在
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    results.append(check("03. 必須列の存在", len(missing_cols) == 0, f"missing={missing_cols}"))

    # 以降は列が存在する前提
    if missing_cols:
        print("[WARN] 必須列が不足しているため一部チェックをスキップします")

    # 4. reserv_noのユニーク性
    if "reserv_no" in df.columns:
        dup = df["reserv_no"].duplicated().sum()
        results.append(check("04. reserv_no のユニーク性", dup == 0, f"duplicates={dup}"))
    else:
        results.append(check("04. reserv_no のユニーク性", False, "column missing"))

    # 5. 日付フォーマット YYYY-MM-DD
    if "reserv_date" in df.columns:
        date_ok = df["reserv_date"].str.match(r"^\d{4}-\d{2}-\d{2}$", na=False).all()
        results.append(check("05. 日付フォーマット YYYY-MM-DD", date_ok))
    else:
        results.append(check("05. 日付フォーマット YYYY-MM-DD", False, "column missing"))

    # 6. store_name が3種類
    if "store_name" in df.columns:
        n_stores = df["store_name"].nunique()
        results.append(check("06. store_name が3種類", n_stores == 3, f"actual={n_stores}"))
    else:
        results.append(check("06. store_name が3種類", False, "column missing"))

    # 7. course が4種類
    if "course" in df.columns:
        n_courses = df["course"].nunique()
        results.append(check("07. course が4種類", n_courses == 4, f"actual={n_courses}"))
    else:
        results.append(check("07. course が4種類", False, "column missing"))

    # 8. guest_count >= 1
    if "guest_count_num" in df.columns:
        gc_ok = (df["guest_count_num"] >= 1).all()
        results.append(check("08. guest_count >= 1", gc_ok))
    else:
        results.append(check("08. guest_count >= 1", False, "column missing"))

    # 9. amount >= 0
    if "amount_num" in df.columns:
        amt_ok = (df["amount_num"] >= 0).all()
        results.append(check("09. amount >= 0", amt_ok))
    else:
        results.append(check("09. amount >= 0", False, "column missing"))

    # 10. status が有効値のみ
    if "status" in df.columns:
        invalid_status = ~df["status"].isin(VALID_STATUSES)
        results.append(check("10. status が有効値のみ", not invalid_status.any(), f"invalid_count={invalid_status.sum()}"))
    else:
        results.append(check("10. status が有効値のみ", False, "column missing"))

    # 11. is_cancel が 0 または 1 のみ
    if "is_cancel_num" in df.columns:
        ic_ok = df["is_cancel_num"].isin([0, 1]).all()
        results.append(check("11. is_cancel が 0 または 1 のみ", ic_ok))
    else:
        results.append(check("11. is_cancel が 0 または 1 のみ", False, "column missing"))

    # 12. loss_amount >= 0
    if "loss_amount_num" in df.columns:
        la_ok = (df["loss_amount_num"] >= 0).all()
        results.append(check("12. loss_amount >= 0", la_ok))
    else:
        results.append(check("12. loss_amount >= 0", False, "column missing"))

    # 13. day_of_week が7種類以下
    if "day_of_week" in df.columns:
        n_dow = df["day_of_week"].nunique()
        results.append(check("13. day_of_week が7種類以下", n_dow <= 7, f"actual={n_dow}"))
    else:
        results.append(check("13. day_of_week が7種類以下", False, "column missing"))

    # 14. source_file 列の存在
    results.append(check("14. source_file 列の存在", "source_file" in df.columns))

    # 15. 欠損率 <= 15% (cancel_reason列を除く)
    check_cols = [c for c in REQUIRED_COLUMNS if c != "cancel_reason" and c in df.columns]
    if check_cols:
        missing_rates = df[check_cols].isnull().mean()
        max_missing = missing_rates.max()
        results.append(check("15. 欠損率 <= 15% (cancel_reason 除く)", max_missing <= 0.15, f"max_missing_rate={max_missing:.3f}"))
    else:
        results.append(check("15. 欠損率 <= 15% (cancel_reason 除く)", False, "no columns to check"))

    # 16. source_file が3種類
    if "source_file" in df.columns:
        n_src = df["source_file"].nunique()
        results.append(check("16. source_file が3種類", n_src == 3, f"actual={n_src}"))
    else:
        results.append(check("16. source_file が3種類", False, "column missing"))

    # 17. キャンセル件数 >= 1
    if "is_cancel_num" in df.columns:
        n_cancel = (df["is_cancel_num"] == 1).sum()
        results.append(check("17. キャンセル件数 >= 1", n_cancel >= 1, f"cancel_count={n_cancel}"))
    else:
        results.append(check("17. キャンセル件数 >= 1", False, "column missing"))

    # 18. 来店済み件数 >= 1
    if "status" in df.columns:
        n_visited = (df["status"] == "来店済み").sum()
        results.append(check("18. 来店済み件数 >= 1", n_visited >= 1, f"visited_count={n_visited}"))
    else:
        results.append(check("18. 来店済み件数 >= 1", False, "column missing"))

    # サマリー
    pass_count = sum(results)
    total = len(results)
    print(f"\nResult: {pass_count}/{total} checks passed")

    if pass_count < total:
        sys.exit(1)


if __name__ == "__main__":
    main()

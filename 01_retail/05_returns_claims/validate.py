# -*- coding: utf-8 -*-
"""
C-34 返品・クレームデータ集計レポートパイプライン
クレンジング出力バリデーションスクリプト

cleaned_claims_202401.csv に対して 18 項目のチェックを実施する。
絵文字・em-dash・記号は使わず [PASS]/[FAIL] を使う。
"""

import sys
import re
import pandas as pd
from pathlib import Path

EXPECTED_STORES = {"渋谷店", "新宿店", "池袋店", "銀座店", "上野店"}
EXPECTED_CATEGORIES = {"食料品", "日用品", "衣料品", "家電", "雑貨"}
EXPECTED_CLAIM_TYPES = {"品質不良", "サイズ不一致", "破損", "その他"}
EXPECTED_RESPONSE_LEVELS = {"迅速", "標準", "遅延"}
REQUIRED_COLUMNS = [
    "receipt_date", "case_no", "store_name", "category",
    "claim_type", "return_amount", "response_days", "resolved_flag",
    "is_resolved", "response_level", "source_file",
]
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def check(label: str, condition: bool) -> bool:
    status = "[PASS]" if condition else "[FAIL]"
    print(f"{status} {label}")
    return condition


def main() -> None:
    base_dir = Path(__file__).parent
    csv_path = base_dir / "output" / "cleaned_claims_202401.csv"

    results = []

    # 1. ファイル存在確認
    results.append(check("01. CSVファイルが存在する", csv_path.exists()))
    if not csv_path.exists():
        print("[ERROR] ファイルが見つからないため以降のチェックをスキップします。")
        sys.exit(1)

    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    # 2. 行数
    results.append(check(f"02. 行数 >= 400 (実際: {len(df)})", len(df) >= 400))

    # 3. 必須列の存在
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    results.append(check(f"03. 必須列がすべて存在する (不足: {missing_cols})", len(missing_cols) == 0))

    # 4. case_no のユニーク性
    dup_count = df["case_no"].duplicated().sum() if "case_no" in df.columns else -1
    results.append(check(f"04. case_no が一意である (重複: {dup_count})", dup_count == 0))

    # 5. 日付フォーマット YYYY-MM-DD
    if "receipt_date" in df.columns:
        bad_dates = df["receipt_date"].astype(str).apply(lambda d: not bool(DATE_PATTERN.match(d))).sum()
        results.append(check(f"05. 日付フォーマットが YYYY-MM-DD (不正: {bad_dates})", bad_dates == 0))
    else:
        results.append(check("05. 日付フォーマットが YYYY-MM-DD", False))

    # 6. store_name が 5 種類
    if "store_name" in df.columns:
        actual_stores = set(df["store_name"].unique())
        results.append(check(
            f"06. store_name が 5 種類 (実際: {sorted(actual_stores)})",
            actual_stores == EXPECTED_STORES,
        ))
    else:
        results.append(check("06. store_name が 5 種類", False))

    # 7. category が 5 種類
    if "category" in df.columns:
        actual_cats = set(df["category"].unique())
        results.append(check(
            f"07. category が 5 種類 (実際: {sorted(actual_cats)})",
            actual_cats == EXPECTED_CATEGORIES,
        ))
    else:
        results.append(check("07. category が 5 種類", False))

    # 8. claim_type が 4 種類
    if "claim_type" in df.columns:
        actual_types = set(df["claim_type"].unique())
        results.append(check(
            f"08. claim_type が 4 種類 (実際: {sorted(actual_types)})",
            actual_types == EXPECTED_CLAIM_TYPES,
        ))
    else:
        results.append(check("08. claim_type が 4 種類", False))

    # 9. return_amount >= 0
    if "return_amount" in df.columns:
        neg_count = (df["return_amount"] < 0).sum()
        results.append(check(f"09. return_amount >= 0 (負の値: {neg_count})", neg_count == 0))
    else:
        results.append(check("09. return_amount >= 0", False))

    # 10. response_days > 0
    if "response_days" in df.columns:
        zero_or_neg = (df["response_days"] <= 0).sum()
        results.append(check(f"10. response_days > 0 (不正: {zero_or_neg})", zero_or_neg == 0))
    else:
        results.append(check("10. response_days > 0", False))

    # 11. is_resolved が 0 または 1 のみ
    if "is_resolved" in df.columns:
        invalid_flag = (~df["is_resolved"].isin([0, 1])).sum()
        results.append(check(f"11. is_resolved が 0/1 のみ (不正: {invalid_flag})", invalid_flag == 0))
    else:
        results.append(check("11. is_resolved が 0/1 のみ", False))

    # 12. response_level が 3 値のみ
    if "response_level" in df.columns:
        invalid_level = (~df["response_level"].isin(EXPECTED_RESPONSE_LEVELS)).sum()
        results.append(check(
            f"12. response_level が 迅速/標準/遅延 のみ (不正: {invalid_level})",
            invalid_level == 0,
        ))
    else:
        results.append(check("12. response_level が 迅速/標準/遅延 のみ", False))

    # 13. 未解決件数 >= 1
    if "is_resolved" in df.columns:
        unresolved = (df["is_resolved"] == 0).sum()
        results.append(check(f"13. 未解決件数 >= 1 (実際: {unresolved})", unresolved >= 1))
    else:
        results.append(check("13. 未解決件数 >= 1", False))

    # 14. 遅延対応件数 >= 1
    if "response_level" in df.columns:
        delayed = (df["response_level"] == "遅延").sum()
        results.append(check(f"14. 遅延対応件数 >= 1 (実際: {delayed})", delayed >= 1))
    else:
        results.append(check("14. 遅延対応件数 >= 1", False))

    # 15. source_file 列の存在
    results.append(check("15. source_file 列が存在する", "source_file" in df.columns))

    # 16. 欠損率 <= 15%
    if len(df) > 0:
        missing_rate = df.isnull().sum().sum() / (len(df) * len(df.columns))
        results.append(check(
            f"16. 欠損率 <= 15% (実際: {missing_rate:.2%})",
            missing_rate <= 0.15,
        ))
    else:
        results.append(check("16. 欠損率 <= 15%", False))

    # 17. source_file が 3 種類
    if "source_file" in df.columns:
        source_count = df["source_file"].nunique()
        results.append(check(
            f"17. source_file が 3 種類 (実際: {source_count})",
            source_count == 3,
        ))
    else:
        results.append(check("17. source_file が 3 種類", False))

    # 18. 解決率 >= 70%
    if "is_resolved" in df.columns and len(df) > 0:
        resolve_rate = df["is_resolved"].mean()
        results.append(check(
            f"18. 解決率 >= 70% (実際: {resolve_rate:.2%})",
            resolve_rate >= 0.70,
        ))
    else:
        results.append(check("18. 解決率 >= 70%", False))

    # サマリー
    passed = sum(results)
    total = len(results)
    print(f"\n[SUMMARY] {passed}/{total} checks passed")
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
validate.py
cleaned_purchases_202401.csv に対して18項目以上のバリデーションを実施する。
print文に絵文字・em-dash・円記号を使わない。[PASS]/[FAIL] を使う。
"""

import pandas as pd
from pathlib import Path
import sys

BASE_DIR = Path(__file__).parent
OUTPUT_FILE = BASE_DIR / "output" / "cleaned_purchases_202401.csv"

VALID_STORES = {"渋谷店", "新宿店", "池袋店"}
VALID_CATEGORIES = {"食料品", "日用品", "衣料品", "家電", "雑貨"}


def check(label: str, condition: bool, detail: str = "") -> bool:
    status = "[PASS]" if condition else "[FAIL]"
    msg = f"{status} {label}"
    if detail:
        msg += f" | {detail}"
    print(msg)
    return condition


def main():
    results = []

    # 1. CSVファイル存在確認
    exists = OUTPUT_FILE.exists()
    results.append(check("CSVファイル存在確認", exists, str(OUTPUT_FILE)))
    if not exists:
        print("[FAIL] CSVが存在しないため以降のチェックをスキップします")
        sys.exit(1)

    df = pd.read_csv(OUTPUT_FILE, encoding="utf-8-sig")

    # 2. 行数 >= 400
    row_count = len(df)
    results.append(check("行数 >= 400", row_count >= 400, f"実際の行数={row_count}"))

    # 3. 必須列の存在（5列）
    required = ["order_date", "customer_code", "category", "amount", "store_name"]
    missing_cols = [c for c in required if c not in df.columns]
    results.append(check("必須列の存在（5列）", len(missing_cols) == 0, f"不足列={missing_cols}"))

    # 4. 日付フォーマット YYYY-MM-DD
    date_fmt_ok = df["order_date"].str.match(r"^\d{4}-\d{2}-\d{2}$").all()
    results.append(check("日付フォーマット YYYY-MM-DD", date_fmt_ok))

    # 5. customer_codeが50種類以上
    n_customers = df["customer_code"].nunique()
    results.append(check("customer_code 種類数 >= 50", n_customers >= 50, f"実際={n_customers}"))

    # 6. categoryが5種類
    n_categories = df["category"].nunique()
    results.append(check("category 種類数 == 5", n_categories == 5, f"実際={n_categories}"))

    # 7. store_nameが3種類
    n_stores = df["store_name"].nunique()
    results.append(check("store_name 種類数 == 3", n_stores == 3, f"実際={n_stores}"))

    # 8. amount > 0（全行）
    all_positive = (df["amount"] > 0).all()
    results.append(check("amount > 0 (全行)", all_positive))

    # 9. amountの最大値 <= 100000（異常値チェック）
    max_amount = df["amount"].max()
    results.append(check("amount 最大値 <= 100000", max_amount <= 100000, f"最大値={max_amount}"))

    # 10. source_file列の存在
    results.append(check("source_file列の存在", "source_file" in df.columns))

    # 11. 欠損率 <= 15%
    missing_rate = df.isnull().mean().max()
    results.append(check("欠損率 <= 15%", missing_rate <= 0.15, f"最大欠損率={missing_rate:.2%}"))

    # 12. source_fileが3種類
    if "source_file" in df.columns:
        n_sources = df["source_file"].nunique()
        results.append(check("source_file が 3 種類", n_sources == 3, f"実際={n_sources}"))
    else:
        results.append(check("source_file が 3 種類", False, "source_file列なし"))

    # 13. customer_codeのフォーマット（CUST-で始まる）
    cust_fmt_ok = df["customer_code"].str.startswith("CUST-").all()
    results.append(check("customer_code が CUST- で始まる", cust_fmt_ok))

    # 14. store_nameが有効値のみ
    invalid_stores = set(df["store_name"].unique()) - VALID_STORES
    results.append(check("store_name が有効値のみ", len(invalid_stores) == 0, f"無効値={invalid_stores}"))

    # 15. categoryが有効値のみ
    invalid_cats = set(df["category"].unique()) - VALID_CATEGORIES
    results.append(check("category が有効値のみ", len(invalid_cats) == 0, f"無効値={invalid_cats}"))

    # 16. order_dateが2024年のデータのみ
    years = df["order_date"].str[:4].unique().tolist()
    only_2024 = all(y == "2024" for y in years)
    results.append(check("order_date が 2024 年のみ", only_2024, f"年の一覧={years}"))

    # 17. 1顧客あたり平均 >= 2件の購買履歴
    avg_per_customer = row_count / max(n_customers, 1)
    results.append(check("1顧客あたり平均購買件数 >= 2", avg_per_customer >= 2, f"平均={avg_per_customer:.2f}"))

    # 18. amountの平均値が 3000~30000 の範囲
    avg_amount = df["amount"].mean()
    results.append(check("amount 平均値 3000 ~ 30000", 3000 <= avg_amount <= 30000, f"平均={avg_amount:.0f}"))

    # サマリー
    passed = sum(results)
    total = len(results)
    print()
    print(f"バリデーション結果: {passed}/{total} 項目 PASS")
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()

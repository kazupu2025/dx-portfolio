# -*- coding: utf-8 -*-
"""
C-34 返品・クレームデータ集計レポートパイプライン
サンプルデータ生成スクリプト

3スタイルのCSVを data/ フォルダに生成する。
"""

import random
import csv
from pathlib import Path
from datetime import date, timedelta

random.seed(42)

# ---- 定数 ----------------------------------------------------------------
STORES = ["渋谷店", "新宿店", "池袋店", "銀座店", "上野店"]
CATEGORIES = ["食料品", "日用品", "衣料品", "家電", "雑貨"]
CLAIM_TYPES = ["品質不良", "サイズ不一致", "破損", "その他"]

START_DATE = date(2024, 1, 1)
END_DATE = date(2024, 1, 31)

ROWS_PER_FILE = 140  # 3ファイルで合計420行


def random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def make_row_core(case_no: str) -> dict:
    """共通フィールドを生成して返す。"""
    resolved = 1 if random.random() < 0.85 else 0
    response_days = random.randint(1, 30) if resolved else random.randint(15, 60)
    receipt_dt = random_date(START_DATE, END_DATE)
    return {
        "receipt_date": receipt_dt,
        "case_no": case_no,
        "store_name": random.choice(STORES),
        "category": random.choice(CATEGORIES),
        "claim_type": random.choice(CLAIM_TYPES),
        "return_amount": round(random.uniform(300, 50000), 0),
        "response_days": response_days,
        "resolved_flag": resolved,
    }


def gen_style_a(data_dir: Path) -> None:
    """スタイルA: 標準日本語列名, 日付 YYYY/MM/DD"""
    filepath = data_dir / "claims_styleA_202401.csv"
    headers = [
        "受付日", "案件番号", "店舗名", "商品カテゴリ",
        "クレーム区分", "返品金額", "対応日数", "解決フラグ",
    ]
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for i in range(ROWS_PER_FILE):
            case_no = f"A-{i+1:04d}"
            r = make_row_core(case_no)
            writer.writerow([
                r["receipt_date"].strftime("%Y/%m/%d"),
                r["case_no"],
                r["store_name"],
                r["category"],
                r["claim_type"],
                int(r["return_amount"]),
                r["response_days"],
                r["resolved_flag"],
            ])
    print(f"[DONE] {filepath}")


def gen_style_b(data_dir: Path) -> None:
    """スタイルB: 英語列名, 日付 YYYY-MM-DD"""
    filepath = data_dir / "claims_styleB_202401.csv"
    headers = [
        "ReceiptDate", "CaseNo", "StoreName", "Category",
        "ClaimType", "ReturnAmount", "ResponseDays", "ResolvedFlag",
    ]
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for i in range(ROWS_PER_FILE):
            case_no = f"B-{i+1:04d}"
            r = make_row_core(case_no)
            writer.writerow([
                r["receipt_date"].strftime("%Y-%m-%d"),
                r["case_no"],
                r["store_name"],
                r["category"],
                r["claim_type"],
                int(r["return_amount"]),
                r["response_days"],
                r["resolved_flag"],
            ])
    print(f"[DONE] {filepath}")


def gen_style_c(data_dir: Path) -> None:
    """スタイルC: バリアント日本語列名, 日付 YYYY/MM/DD"""
    filepath = data_dir / "claims_styleC_202401.csv"
    headers = [
        "日付", "受付番号", "店舗", "品目区分",
        "理由区分", "返金額", "処理日数", "完了フラグ",
    ]
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for i in range(ROWS_PER_FILE):
            case_no = f"C-{i+1:04d}"
            r = make_row_core(case_no)
            writer.writerow([
                r["receipt_date"].strftime("%Y/%m/%d"),
                r["case_no"],
                r["store_name"],
                r["category"],
                r["claim_type"],
                int(r["return_amount"]),
                r["response_days"],
                r["resolved_flag"],
            ])
    print(f"[DONE] {filepath}")


def main() -> None:
    base_dir = Path(__file__).parent
    data_dir = base_dir / "data"
    data_dir.mkdir(exist_ok=True)

    gen_style_a(data_dir)
    gen_style_b(data_dir)
    gen_style_c(data_dir)

    total = ROWS_PER_FILE * 3
    print(f"[INFO] Total rows generated: {total}")


if __name__ == "__main__":
    main()

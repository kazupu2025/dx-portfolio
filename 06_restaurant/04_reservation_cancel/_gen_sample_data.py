# -*- coding: utf-8 -*-
"""
C-38: 予約キャンセル集計・傾向分析パイプライン
サンプルデータ生成スクリプト
3スタイルのCSVを data/ フォルダに生成する
"""

import random
import csv
import os
from pathlib import Path

random.seed(42)

# 出力先
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# マスタデータ
STORES = ["渋谷店", "新宿店", "銀座店"]
COURSES = ["ランチ", "ディナー", "飲み放題", "個室コース"]
CANCEL_REASONS = ["急用", "体調不良", "天候", "忘れ", "その他"]
# ステータス比率: キャンセル20%, 来店済み70%, 予約済み10%
STATUS_WEIGHTS = [("キャンセル", 0.20), ("来店済み", 0.70), ("予約済み", 0.10)]

# コース別金額レンジ
COURSE_AMOUNT = {
    "ランチ": (2000, 4000),
    "ディナー": (5000, 12000),
    "飲み放題": (3000, 6000),
    "個室コース": (8000, 20000),
}

ROWS_PER_STYLE = 140


def pick_status():
    r = random.random()
    cumulative = 0.0
    for status, weight in STATUS_WEIGHTS:
        cumulative += weight
        if r < cumulative:
            return status
    return "来店済み"


def gen_date_slash(year=2024, month=1):
    """YYYY/MM/DD フォーマットの日付を生成"""
    day = random.randint(1, 28)
    return f"{year}/{month:02d}/{day:02d}"


def gen_date_dash(year=2024, month=1):
    """YYYY-MM-DD フォーマットの日付を生成"""
    day = random.randint(1, 28)
    return f"{year}-{month:02d}-{day:02d}"


def gen_row_base(i, month_offset=0):
    """共通の予約データを生成"""
    month = 1 + month_offset
    store = random.choice(STORES)
    course = random.choice(COURSES)
    guest_count = random.randint(1, 10)
    amount_lo, amount_hi = COURSE_AMOUNT[course]
    amount = random.randint(amount_lo // 1000, amount_hi // 1000) * 1000 * guest_count
    status = pick_status()
    cancel_reason = random.choice(CANCEL_REASONS) if status == "キャンセル" else None
    return store, course, guest_count, amount, status, cancel_reason, month


def gen_style_a(n=ROWS_PER_STYLE):
    """スタイルA: 標準日本語列名、日付 YYYY/MM/DD"""
    rows = []
    for i in range(n):
        store, course, guest_count, amount, status, cancel_reason, month = gen_row_base(i)
        reserv_date = gen_date_slash(2024, month)
        reserv_no = f"A{i+1:05d}"
        rows.append({
            "予約日": reserv_date,
            "予約番号": reserv_no,
            "店舗名": store,
            "コース": course,
            "予約人数": guest_count,
            "予約金額": amount,
            "ステータス": status,
            "キャンセル理由": cancel_reason if cancel_reason else "",
        })
    return rows


def gen_style_b(n=ROWS_PER_STYLE):
    """スタイルB: 英語列名、日付 YYYY-MM-DD"""
    rows = []
    for i in range(n):
        store, course, guest_count, amount, status, cancel_reason, month = gen_row_base(i)
        reserv_date = gen_date_dash(2024, month)
        reserv_no = f"B{i+1:05d}"
        rows.append({
            "ReservDate": reserv_date,
            "ReservNo": reserv_no,
            "StoreName": store,
            "Course": course,
            "GuestCount": guest_count,
            "Amount": amount,
            "Status": status,
            "CancelReason": cancel_reason if cancel_reason else "",
        })
    return rows


def gen_style_c(n=ROWS_PER_STYLE):
    """スタイルC: バリアント日本語列名、日付 YYYY/MM/DD"""
    rows = []
    for i in range(n):
        store, course, guest_count, amount, status, cancel_reason, month = gen_row_base(i)
        reserv_date = gen_date_slash(2024, month)
        reserv_no = f"C{i+1:05d}"
        rows.append({
            "日付": reserv_date,
            "管理番号": reserv_no,
            "店舗": store,
            "コース区分": course,
            "人数": guest_count,
            "金額": amount,
            "状態": status,
            "理由": cancel_reason if cancel_reason else "",
        })
    return rows


def write_csv(filepath, rows):
    if not rows:
        return
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] Written: {filepath} ({len(rows)} rows)")


def main():
    DATA_DIR.mkdir(exist_ok=True)

    rows_a = gen_style_a()
    rows_b = gen_style_b()
    rows_c = gen_style_c()

    write_csv(DATA_DIR / "reservations_styleA_202401.csv", rows_a)
    write_csv(DATA_DIR / "reservations_styleB_202401.csv", rows_b)
    write_csv(DATA_DIR / "reservations_styleC_202401.csv", rows_c)

    total = len(rows_a) + len(rows_b) + len(rows_c)
    print(f"[OK] Total rows generated: {total}")
    assert total >= 420, f"Total rows {total} < 420"


if __name__ == "__main__":
    main()

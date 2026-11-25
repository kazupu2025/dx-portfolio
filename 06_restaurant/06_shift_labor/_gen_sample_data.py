# -*- coding: utf-8 -*-
"""
C-40: アルバイトシフト管理・人件費集計パイプライン
サンプルデータ生成スクリプト
3スタイルのCSVを data/ フォルダに生成（各140行、合計420行）
"""

import random
import csv
import os
from pathlib import Path

random.seed(42)

# ---- 定数定義 ----
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

STAFF_IDS = [f"ST-{str(i).zfill(3)}" for i in range(1, 21)]  # ST-001 ~ ST-020
STORES = ["渋谷店", "新宿店", "銀座店"]
ROLES = ["ホール", "キッチン", "レジ"]

ROWS_PER_FILE = 140

# 2024年1月の日付（平日・週末含む）
DATES_SLASH = [f"2024/01/{str(d).zfill(2)}" for d in range(1, 32) if d <= 31]
DATES_DASH = [f"2024-01-{str(d).zfill(2)}" for d in range(1, 32) if d <= 31]


def rand_time_pair():
    """出勤・退勤時刻ペアと実働時間を返す"""
    start_hour = random.randint(8, 18)
    work_hours = round(random.uniform(3.0, 9.0), 1)
    end_hour = start_hour + int(work_hours)
    end_min = int((work_hours % 1) * 60)
    start_str = f"{str(start_hour).zfill(2)}:00"
    end_str = f"{str(end_hour).zfill(2)}:{str(end_min).zfill(2)}"
    return start_str, end_str, work_hours


def rand_hourly_rate():
    """1000〜1500円の時給をランダムに返す"""
    return random.randint(1000, 1500)


def generate_row_base():
    """共通ランダム値を生成"""
    date_idx = random.randint(0, len(DATES_SLASH) - 1)
    staff_id = random.choice(STAFF_IDS)
    store = random.choice(STORES)
    role = random.choice(ROLES)
    start, end, hours = rand_time_pair()
    rate = rand_hourly_rate()
    return date_idx, staff_id, store, role, start, end, hours, rate


# ---- スタイルA: 標準日本語列名（日付: YYYY/MM/DD）----
def generate_style_a():
    rows = []
    for _ in range(ROWS_PER_FILE):
        date_idx, staff_id, store, role, start, end, hours, rate = generate_row_base()
        rows.append({
            "勤務日": DATES_SLASH[date_idx],
            "スタッフID": staff_id,
            "店舗名": store,
            "役職": role,
            "出勤時刻": start,
            "退勤時刻": end,
            "実働時間": hours,
            "時給": rate,
        })
    return rows


# ---- スタイルB: 英語列名（日付: YYYY-MM-DD）----
def generate_style_b():
    rows = []
    for _ in range(ROWS_PER_FILE):
        date_idx, staff_id, store, role, start, end, hours, rate = generate_row_base()
        rows.append({
            "WorkDate": DATES_DASH[date_idx],
            "StaffID": staff_id,
            "StoreName": store,
            "Role": role,
            "StartTime": start,
            "EndTime": end,
            "WorkHours": hours,
            "HourlyRate": rate,
        })
    return rows


# ---- スタイルC: バリアント日本語（日付: YYYY/MM/DD）----
def generate_style_c():
    rows = []
    for _ in range(ROWS_PER_FILE):
        date_idx, staff_id, store, role, start, end, hours, rate = generate_row_base()
        rows.append({
            "日付": DATES_SLASH[date_idx],
            "従業員番号": staff_id,
            "店舗": store,
            "ポジション": role,
            "開始": start,
            "終了": end,
            "勤務時間": hours,
            "時給単価": rate,
        })
    return rows


def write_csv(rows, filepath, encoding="utf-8-sig"):
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with open(filepath, "w", newline="", encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    style_a = generate_style_a()
    style_b = generate_style_b()
    style_c = generate_style_c()

    write_csv(style_a, DATA_DIR / "shift_styleA_202401.csv")
    write_csv(style_b, DATA_DIR / "shift_styleB_202401.csv")
    write_csv(style_c, DATA_DIR / "shift_styleC_202401.csv")

    print(f"[OK] スタイルA: {len(style_a)} 行 -> data/shift_styleA_202401.csv")
    print(f"[OK] スタイルB: {len(style_b)} 行 -> data/shift_styleB_202401.csv")
    print(f"[OK] スタイルC: {len(style_c)} 行 -> data/shift_styleC_202401.csv")
    print(f"[OK] 合計: {len(style_a) + len(style_b) + len(style_c)} 行")


if __name__ == "__main__":
    main()

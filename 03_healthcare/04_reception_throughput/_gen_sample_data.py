# -*- coding: utf-8 -*-
"""
C-37: 来客記録データ集計・スループット分析パイプライン
サンプルデータ生成スクリプト
3スタイルのCSVを data/ フォルダに生成する（合計420行以上）
"""

import random
import csv
from pathlib import Path
from datetime import date, timedelta, time

random.seed(42)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DEPARTMENTS = ["内科", "外科", "整形外科", "小児科", "眼科"]

# 基準日
START_DATE = date(2024, 1, 1)
END_DATE = date(2024, 1, 31)


def random_date():
    delta = (END_DATE - START_DATE).days
    return START_DATE + timedelta(days=random.randint(0, delta))


def random_arrival_hour():
    """8:00〜16:00 の間で到着時刻の時を返す（診察枠は8〜17時）"""
    return random.randint(8, 16)


def make_record(index, rec_date):
    dept = DEPARTMENTS[index % len(DEPARTMENTS)]
    arrival_h = random_arrival_hour()
    arrival_m = random.randint(0, 59)

    # 待ち時間: 5〜90分、15%の確率で60分超の長待ち
    if random.random() < 0.15:
        wait_min = random.randint(61, 90)
    else:
        wait_min = random.randint(5, 60)

    # 診察時間: 5〜45分
    treat_min = random.randint(5, 45)

    arrival_time = time(arrival_h, arrival_m)
    start_h = arrival_h
    start_m = arrival_m + wait_min
    while start_m >= 60:
        start_m -= 60
        start_h += 1
    if start_h >= 24:
        start_h = 23
        start_m = 59
    start_time = time(start_h, start_m)

    end_h = start_h
    end_m = start_m + treat_min
    while end_m >= 60:
        end_m -= 60
        end_h += 1
    if end_h >= 24:
        end_h = 23
        end_m = 59
    end_time = time(end_h, end_m)

    return {
        "rec_date": rec_date,
        "reception_no": f"R{index + 1:05d}",
        "department": dept,
        "arrival_time": arrival_time,
        "start_time": start_time,
        "end_time": end_time,
        "wait_minutes": wait_min,
        "treat_minutes": treat_min,
    }


# 各スタイル140件生成
N = 140
records_a, records_b, records_c = [], [], []

for i in range(N):
    records_a.append(make_record(i, random_date()))
for i in range(N):
    records_b.append(make_record(N + i, random_date()))
for i in range(N):
    records_c.append(make_record(2 * N + i, random_date()))


# ============================================================
# スタイルA: 標準日本語列名, 日付 YYYY/MM/DD
# ============================================================
path_a = DATA_DIR / "reception_A_202401.csv"
with open(path_a, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["来院日", "受付番号", "診療科", "来院時刻", "診察開始時刻", "診察終了時刻", "待ち時間（分）", "診察時間（分）"])
    for r in records_a:
        writer.writerow([
            r["rec_date"].strftime("%Y/%m/%d"),
            r["reception_no"],
            r["department"],
            r["arrival_time"].strftime("%H:%M"),
            r["start_time"].strftime("%H:%M"),
            r["end_time"].strftime("%H:%M"),
            r["wait_minutes"],
            r["treat_minutes"],
        ])

# ============================================================
# スタイルB: 英語列名, 日付 YYYY-MM-DD
# ============================================================
path_b = DATA_DIR / "reception_B_202401.csv"
with open(path_b, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["VisitDate", "ReceptionNo", "Department", "ArrivalTime", "StartTime", "EndTime", "WaitMinutes", "TreatMinutes"])
    for r in records_b:
        writer.writerow([
            r["rec_date"].strftime("%Y-%m-%d"),
            r["reception_no"],
            r["department"],
            r["arrival_time"].strftime("%H:%M"),
            r["start_time"].strftime("%H:%M"),
            r["end_time"].strftime("%H:%M"),
            r["wait_minutes"],
            r["treat_minutes"],
        ])

# ============================================================
# スタイルC: バリアント日本語列名, 日付 YYYY/MM/DD
# ============================================================
path_c = DATA_DIR / "reception_C_202401.csv"
with open(path_c, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["日付", "整理番号", "科名", "受付時刻", "開始時刻", "終了時刻", "待機分", "診療分"])
    for r in records_c:
        writer.writerow([
            r["rec_date"].strftime("%Y/%m/%d"),
            r["reception_no"],
            r["department"],
            r["arrival_time"].strftime("%H:%M"),
            r["start_time"].strftime("%H:%M"),
            r["end_time"].strftime("%H:%M"),
            r["wait_minutes"],
            r["treat_minutes"],
        ])

total = len(records_a) + len(records_b) + len(records_c)
print(f"[OK] サンプルデータ生成完了: {total} 件")
print(f"  スタイルA: {path_a} ({len(records_a)} 件)")
print(f"  スタイルB: {path_b} ({len(records_b)} 件)")
print(f"  スタイルC: {path_c} ({len(records_c)} 件)")

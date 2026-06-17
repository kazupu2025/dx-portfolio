# -*- coding: utf-8 -*-
import os
import random
import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

ROOM_TYPES_JA = ["シングル", "ツイン", "ダブル", "スイート"]
ROOM_TYPES_EN = ["Single", "Twin", "Double", "Suite"]

STATUS_JA = ["宿泊済み", "キャンセル", "ノーショウ"]
STATUS_WEIGHTS = [0.75, 0.20, 0.05]

CANCEL_REASONS_JA = ["予定変更", "体調不良", "料金が高い", "他のホテルに変更", "天候不良"]
CANCEL_REASONS_EN = ["Schedule change", "Illness", "Price too high", "Changed hotel", "Bad weather"]

ROOM_RATE_RANGES = {
    "シングル": (8000, 20000),
    "ツイン": (15000, 35000),
    "ダブル": (18000, 40000),
    "スイート": (40000, 80000),
}
ROOM_RATE_EN = {
    "Single": (8000, 20000),
    "Twin": (15000, 35000),
    "Double": (18000, 40000),
    "Suite": (40000, 80000),
}

N = 480
dates = pd.date_range("2024-01-01", "2024-01-20", freq="D")


def generate_records():
    records = []
    for i in range(N):
        reserv_no = f"RES-{i+1:04d}"
        room_type_idx = random.randint(0, 3)
        room_type_ja = ROOM_TYPES_JA[room_type_idx]
        room_type_en = ROOM_TYPES_EN[room_type_idx]
        guest_count = random.randint(1, 4)
        nights = random.randint(1, 5)
        lo, hi = ROOM_RATE_RANGES[room_type_ja]
        room_rate = random.randint(lo // 1000, hi // 1000) * 1000
        status_idx = np.random.choice(3, p=STATUS_WEIGHTS)
        status_ja = STATUS_JA[status_idx]
        checkin_date = random.choice(dates)
        if status_ja in ["キャンセル", "ノーショウ"]:
            cancel_reason_ja = random.choice(CANCEL_REASONS_JA)
            cancel_reason_en = CANCEL_REASONS_EN[CANCEL_REASONS_JA.index(cancel_reason_ja)]
        else:
            cancel_reason_ja = ""
            cancel_reason_en = ""
        records.append({
            "checkin_date": checkin_date,
            "reserv_no": reserv_no,
            "room_type_ja": room_type_ja,
            "room_type_en": room_type_en,
            "guest_count": guest_count,
            "nights": nights,
            "room_rate": room_rate,
            "status_ja": status_ja,
            "status_idx": status_idx,
            "cancel_reason_ja": cancel_reason_ja,
            "cancel_reason_en": cancel_reason_en,
        })
    return records


records = generate_records()

# 3スタイルに分割（各160件、reserv_noが重複しないよう分ける）
n = len(records)
split1 = n // 3
split2 = 2 * n // 3

# StyleA: Standard Japanese, date YYYY/MM/DD (records[0:split1])
rows_a = []
for r in records[:split1]:
    rows_a.append({
        "チェックイン日": r["checkin_date"].strftime("%Y/%m/%d"),
        "予約番号": r["reserv_no"],
        "客室タイプ": r["room_type_ja"],
        "人数": r["guest_count"],
        "宿泊数": r["nights"],
        "室料": r["room_rate"],
        "ステータス": r["status_ja"],
        "キャンセル理由": r["cancel_reason_ja"] if r["cancel_reason_ja"] else None,
    })
df_a = pd.DataFrame(rows_a)
df_a.to_csv(os.path.join(DATA_DIR, "reservations_styleA.csv"), index=False, encoding="utf-8-sig")
print("[OK] StyleA saved: reservations_styleA.csv ({} rows)".format(len(df_a)))

# StyleB: English, date YYYY-MM-DD (records[split1:split2])
rows_b = []
for r in records[split1:split2]:
    rows_b.append({
        "CheckinDate": r["checkin_date"].strftime("%Y-%m-%d"),
        "ReservNo": r["reserv_no"],
        "RoomType": r["room_type_en"],
        "GuestCount": r["guest_count"],
        "Nights": r["nights"],
        "RoomRate": r["room_rate"],
        "Status": ["Stayed", "Cancelled", "NoShow"][r["status_idx"]],
        "CancelReason": r["cancel_reason_en"] if r["cancel_reason_en"] else None,
    })
df_b = pd.DataFrame(rows_b)
df_b.to_csv(os.path.join(DATA_DIR, "reservations_styleB.csv"), index=False, encoding="utf-8-sig")
print("[OK] StyleB saved: reservations_styleB.csv ({} rows)".format(len(df_b)))

# StyleC: Variant Japanese, date YYYY/MM/DD (records[split2:])
rows_c = []
for r in records[split2:]:
    rows_c.append({
        "入館日": r["checkin_date"].strftime("%Y/%m/%d"),
        "予約ID": r["reserv_no"],
        "部屋種別": r["room_type_ja"],
        "泊数": r["nights"],
        "宿泊者数": r["guest_count"],
        "料金": r["room_rate"],
        "状態": r["status_ja"],
        "解約理由": r["cancel_reason_ja"] if r["cancel_reason_ja"] else None,
    })
df_c = pd.DataFrame(rows_c)
df_c.to_csv(os.path.join(DATA_DIR, "reservations_styleC.csv"), index=False, encoding="utf-8-sig")
print("[OK] StyleC saved: reservations_styleC.csv ({} rows)".format(len(df_c)))
print("[OK] Sample data generation complete.")

# -*- coding: utf-8 -*-
import os
import pandas as pd
import numpy as np

random_seed = 42

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CANONICAL_COLS = [
    "checkin_date", "reserv_no", "room_type", "guest_count", "nights",
    "room_rate", "status", "cancel_reason", "total_revenue", "is_cancel",
    "loss_revenue", "revenue_per_guest", "source_file"
]

COLUMN_MAP = {
    # StyleA: Standard Japanese
    "チェックイン日": "checkin_date",
    "予約番号": "reserv_no",
    "客室タイプ": "room_type",
    "人数": "guest_count",
    "宿泊数": "nights",
    "室料": "room_rate",
    "ステータス": "status",
    "キャンセル理由": "cancel_reason",
    # StyleB: English
    "CheckinDate": "checkin_date",
    "ReservNo": "reserv_no",
    "RoomType": "room_type",
    "GuestCount": "guest_count",
    "Nights": "nights",
    "RoomRate": "room_rate",
    "Status": "status",
    "CancelReason": "cancel_reason",
    # StyleC: Variant Japanese
    "入館日": "checkin_date",
    "予約ID": "reserv_no",
    "部屋種別": "room_type",
    "泊数": "nights",
    "宿泊者数": "guest_count",
    "料金": "room_rate",
    "状態": "status",
    "解約理由": "cancel_reason",
}

STATUS_NORMALIZE = {
    "宿泊済み": "宿泊済み",
    "Stayed": "宿泊済み",
    "キャンセル": "キャンセル",
    "Cancelled": "キャンセル",
    "ノーショウ": "ノーショウ",
    "NoShow": "ノーショウ",
}

ROOM_TYPE_NORMALIZE = {
    "シングル": "シングル",
    "Single": "シングル",
    "ツイン": "ツイン",
    "Twin": "ツイン",
    "ダブル": "ダブル",
    "Double": "ダブル",
    "スイート": "スイート",
    "Suite": "スイート",
}

CANCEL_STATUSES = ["キャンセル", "ノーショウ"]


def load_and_rename(filepath, source_label):
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    df = df.rename(columns=COLUMN_MAP)
    df["source_file"] = source_label
    return df


def normalize_date(series):
    series = series.astype(str).str.replace("/", "-", regex=False)
    return pd.to_datetime(series, format="%Y-%m-%d").dt.strftime("%Y-%m-%d")


def cleanse(df):
    df = df.copy()
    df["checkin_date"] = normalize_date(df["checkin_date"])
    df["guest_count"] = pd.to_numeric(df["guest_count"], errors="coerce").fillna(1).astype(int)
    df["nights"] = pd.to_numeric(df["nights"], errors="coerce").fillna(1).astype(int)
    df["room_rate"] = pd.to_numeric(df["room_rate"], errors="coerce").fillna(0).astype(int)
    df["status"] = df["status"].map(STATUS_NORMALIZE).fillna(df["status"])
    df["room_type"] = df["room_type"].map(ROOM_TYPE_NORMALIZE).fillna(df["room_type"])
    df["cancel_reason"] = df["cancel_reason"].fillna("")

    # Derived columns
    df["total_revenue"] = df.apply(
        lambda r: r["room_rate"] * r["nights"] if r["status"] == "宿泊済み" else 0, axis=1
    )
    df["is_cancel"] = df["status"].apply(lambda s: 1 if s in CANCEL_STATUSES else 0)
    df["loss_revenue"] = df["room_rate"] * df["nights"] * df["is_cancel"]
    df["revenue_per_guest"] = df.apply(
        lambda r: r["total_revenue"] / r["guest_count"]
        if r["guest_count"] > 0 and r["status"] == "宿泊済み" else 0.0,
        axis=1
    )

    return df[CANONICAL_COLS]


files = [
    ("reservations_styleA.csv", "styleA"),
    ("reservations_styleB.csv", "styleB"),
    ("reservations_styleC.csv", "styleC"),
]

dfs = []
for fname, label in files:
    fpath = os.path.join(DATA_DIR, fname)
    df = load_and_rename(fpath, label)
    df = cleanse(df)
    dfs.append(df)
    print("[OK] Loaded and cleansed: {} ({} rows)".format(fname, len(df)))

combined = pd.concat(dfs, ignore_index=True)
out_path = os.path.join(OUTPUT_DIR, "cleaned_reservations_202401.csv")
combined.to_csv(out_path, index=False, encoding="utf-8-sig")
print("[OK] Output written: cleaned_reservations_202401.csv ({} rows)".format(len(combined)))

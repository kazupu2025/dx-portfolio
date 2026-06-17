# -*- coding: utf-8 -*-
import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

COLUMN_MAP = {
    # StyleA (Japanese)
    "シフト日": "shift_date",
    "店舗コード": "store_id",
    "店舗名": "store_name",
    "役割": "role",
    "必要人員": "required_staff",
    "実員数": "actual_staff",
    "勤務時間": "work_hours",
    "時給": "hourly_rate",
    # StyleB (English)
    "ShiftDate": "shift_date",
    "StoreID": "store_id",
    "StoreName": "store_name",
    "Role": "role",
    "RequiredStaff": "required_staff",
    "ActualStaff": "actual_staff",
    "WorkHours": "work_hours",
    "HourlyRate": "hourly_rate",
    # StyleC (Variant Japanese)
    "勤務日": "shift_date",
    "店舗ID": "store_id",
    "店舗": "store_name",
    "ポジション": "role",
    "必要スタッフ数": "required_staff",
    "出勤スタッフ数": "actual_staff",
    "作業時間": "work_hours",
    "賃金": "hourly_rate",
}

CANONICAL_COLS = [
    "shift_date",
    "store_id",
    "store_name",
    "role",
    "required_staff",
    "actual_staff",
    "work_hours",
    "hourly_rate",
    "daily_wage",
    "staffing_gap",
    "is_understaffed",
    "labor_cost_flag",
    "source_file",
]

FILES = [
    "shift_styleA.csv",
    "shift_styleB.csv",
    "shift_styleC.csv",
]


def load_and_normalize(filepath):
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    df = df.rename(columns=COLUMN_MAP)
    df["source_file"] = os.path.basename(filepath)
    return df


def cleanse_df(df):
    # Date normalization
    df["shift_date"] = df["shift_date"].astype(str).str.replace("/", "-", regex=False)
    df["shift_date"] = pd.to_datetime(df["shift_date"], format="%Y-%m-%d").dt.strftime("%Y-%m-%d")

    # Numeric conversion
    for col in ["required_staff", "actual_staff", "work_hours", "hourly_rate"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Derived columns
    df["daily_wage"] = df["actual_staff"] * df["work_hours"] * df["hourly_rate"]
    df["staffing_gap"] = df["actual_staff"] - df["required_staff"]
    df["is_understaffed"] = (df["staffing_gap"] < 0).astype(int)

    # labor_cost_flag
    threshold = df["daily_wage"].quantile(0.75)
    df["labor_cost_flag"] = df["daily_wage"].apply(
        lambda x: "高コスト" if x > threshold else "通常"
    )

    return df


dfs = []
for fname in FILES:
    fpath = os.path.join(DATA_DIR, fname)
    df = load_and_normalize(fpath)
    df = cleanse_df(df)
    dfs.append(df)
    print(f"[OK] Loaded and cleansed: {fname} ({len(df)} rows)")

combined = pd.concat(dfs, ignore_index=True)

# Output only canonical columns
combined = combined[CANONICAL_COLS]

out_path = os.path.join(OUTPUT_DIR, "cleaned_shift_202401.csv")
combined.to_csv(out_path, index=False, encoding="utf-8-sig")
print(f"[OK] Output: {out_path} ({len(combined)} rows)")

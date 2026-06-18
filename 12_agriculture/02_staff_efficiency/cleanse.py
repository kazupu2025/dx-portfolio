# -*- coding: utf-8 -*-
"""
C-59 農場スタッフ勤怠・作業効率分析パイプライン
データクレンジングスクリプト
"""

import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Column mapping for 3 styles ---
COLUMN_MAP = {
    # StyleA
    "作業日": "work_date",
    "記録ID": "record_id",
    "スタッフID": "staff_id",
    "作業区分": "work_type",
    "作物": "crop",
    "作業時間": "work_hours",
    "目標数量": "target_qty",
    "実績数量": "actual_qty",
    "目標達成": "is_target_met",
    # StyleB
    "WorkDate": "work_date",
    "RecordID": "record_id",
    "StaffID": "staff_id",
    "WorkType": "work_type",
    "Crop": "crop",
    "WorkHours": "work_hours",
    "TargetQty": "target_qty",
    "ActualQty": "actual_qty",
    "IsTargetMet": "is_target_met",
    # StyleC
    "日付": "work_date",
    "管理番号": "record_id",
    "作業者ID": "staff_id",
    "作業種別": "work_type",
    "栽培品目": "crop",
    "勤務時間": "work_hours",
    "計画量": "target_qty",
    "収穫量": "actual_qty",
    "達成フラグ": "is_target_met",
}

CANONICAL_COLS = [
    "work_date",
    "record_id",
    "staff_id",
    "work_type",
    "crop",
    "work_hours",
    "target_qty",
    "actual_qty",
    "is_target_met",
    "achievement_rate",
    "productivity",
    "efficiency_grade",
    "source_file",
]


def load_and_rename(filepath):
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    df = df.rename(columns=COLUMN_MAP)
    df["source_file"] = os.path.basename(filepath)
    return df


def normalize_date(series):
    return pd.to_datetime(
        series.astype(str).str.replace("/", "-"),
        format="%Y-%m-%d",
        errors="coerce",
    ).dt.strftime("%Y-%m-%d")


def compute_derived(df):
    df["work_hours"] = pd.to_numeric(df["work_hours"], errors="coerce")
    df["target_qty"] = pd.to_numeric(df["target_qty"], errors="coerce")
    df["actual_qty"] = pd.to_numeric(df["actual_qty"], errors="coerce")

    # Recompute is_target_met from actual vs target
    df["is_target_met"] = (df["actual_qty"] >= df["target_qty"]).astype(int)

    # achievement_rate
    mask_target = df["target_qty"] > 0
    df["achievement_rate"] = np.where(
        mask_target,
        df["actual_qty"] / df["target_qty"],
        np.nan,
    )

    # productivity = actual_qty / work_hours
    mask_hours = df["work_hours"] > 0
    df["productivity"] = np.where(
        mask_hours,
        df["actual_qty"] / df["work_hours"],
        np.nan,
    )

    # efficiency_grade
    def grade(p):
        if pd.isna(p):
            return "低効率"
        if p >= 80:
            return "高効率"
        if p >= 50:
            return "中効率"
        return "低効率"

    df["efficiency_grade"] = df["productivity"].apply(grade)
    return df


def main():
    files = [
        os.path.join(DATA_DIR, "farm_work_styleA.csv"),
        os.path.join(DATA_DIR, "farm_work_styleB.csv"),
        os.path.join(DATA_DIR, "farm_work_styleC.csv"),
    ]

    dfs = []
    for f in files:
        df = load_and_rename(f)
        df["work_date"] = normalize_date(df["work_date"])
        df = compute_derived(df)
        dfs.append(df)
        print(f"[OK] Loaded {os.path.basename(f)}: {len(df)} rows")

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined[CANONICAL_COLS]

    out_path = os.path.join(OUTPUT_DIR, "cleaned_farm_work_202401.csv")
    combined.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[OK] Cleaned data saved: {out_path} ({len(combined)} rows)")


if __name__ == "__main__":
    main()

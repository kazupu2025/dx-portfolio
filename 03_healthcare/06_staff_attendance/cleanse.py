# -*- coding: utf-8 -*-
import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CANONICAL_COLS = [
    "work_date", "record_id", "staff_type", "department", "staff_id",
    "scheduled_hours", "actual_hours", "is_absent", "absence_reason",
    "overtime_hours", "utilization_rate", "attendance_flag", "overtime_flag",
    "source_file"
]

COLUMN_MAP = {
    "styleA": {
        "勤務日": "work_date",
        "記録ID": "record_id",
        "スタッフ種別": "staff_type",
        "診療科": "department",
        "スタッフID": "staff_id",
        "予定時間": "scheduled_hours",
        "実働時間": "actual_hours",
        "欠勤フラグ": "is_absent",
        "欠勤理由": "absence_reason",
        "残業時間": "overtime_hours",
    },
    "styleB": {
        "WorkDate": "work_date",
        "RecordID": "record_id",
        "StaffType": "staff_type",
        "Department": "department",
        "StaffID": "staff_id",
        "ScheduledHours": "scheduled_hours",
        "ActualHours": "actual_hours",
        "IsAbsent": "is_absent",
        "AbsenceReason": "absence_reason",
        "OvertimeHours": "overtime_hours",
    },
    "styleC": {
        "出勤日": "work_date",
        "管理番号": "record_id",
        "職種区分": "staff_type",
        "所属科": "department",
        "職員ID": "staff_id",
        "所定時間": "scheduled_hours",
        "勤務時間": "actual_hours",
        "欠勤": "is_absent",
        "不在理由": "absence_reason",
        "残業": "overtime_hours",
    },
}

FILES = [
    ("attendance_styleA_202401.csv", "styleA"),
    ("attendance_styleB_202401.csv", "styleB"),
    ("attendance_styleC_202401.csv", "styleC"),
]


def normalize_date(s):
    s = s.astype(str).str.replace("/", "-", regex=False)
    return pd.to_datetime(s, format="%Y-%m-%d", errors="coerce").dt.strftime("%Y-%m-%d")


def cleanse_file(filename, style):
    fpath = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(fpath, encoding="utf-8-sig")
    df = df.rename(columns=COLUMN_MAP[style])

    # Date normalization
    df["work_date"] = normalize_date(df["work_date"])

    # Numeric conversion
    for col in ["scheduled_hours", "actual_hours", "is_absent", "overtime_hours"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # absence_reason: empty string -> NaN for absent rows keep value, present rows set NaN
    df["absence_reason"] = df["absence_reason"].replace("", np.nan)
    # For present staff (is_absent == 0), set absence_reason to NaN
    df.loc[df["is_absent"] == 0, "absence_reason"] = np.nan

    # overtime_hours: for absent staff, set to 0
    df.loc[df["is_absent"] == 1, "overtime_hours"] = 0.0
    df["overtime_hours"] = df["overtime_hours"].fillna(0.0)

    # Derived columns
    def calc_utilization(row):
        if row["is_absent"] == 1:
            return 0.0
        if pd.notna(row["scheduled_hours"]) and row["scheduled_hours"] > 0:
            return row["actual_hours"] / row["scheduled_hours"]
        return np.nan

    df["utilization_rate"] = df.apply(calc_utilization, axis=1)
    df["attendance_flag"] = df["is_absent"].apply(lambda x: "欠勤" if x == 1 else "出勤")
    df["overtime_flag"] = df["overtime_hours"].apply(lambda x: "残業あり" if x > 0 else "残業なし")
    df["source_file"] = filename

    df = df[CANONICAL_COLS]
    return df


dfs = []
for fname, style in FILES:
    df = cleanse_file(fname, style)
    dfs.append(df)
    print("[OK] {} => {} rows".format(fname, len(df)))

result = pd.concat(dfs, ignore_index=True)
out_path = os.path.join(OUTPUT_DIR, "cleaned_attendance_202401.csv")
result.to_csv(out_path, index=False, encoding="utf-8-sig")
print("[OK] Output: {} rows => {}".format(len(result), out_path))

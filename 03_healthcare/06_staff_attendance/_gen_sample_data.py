# -*- coding: utf-8 -*-
import random
import numpy as np
import pandas as pd
import os

random.seed(42)
np.random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

STAFF_TYPES_JP = ["医師", "看護師", "薬剤師", "事務"]
DEPARTMENTS_JP = ["内科", "外科", "小児科", "整形外科", "救急"]
STAFF_IDS = ["STAFF-{:02d}".format(i) for i in range(1, 13)]
ABSENCE_REASONS = ["体調不良", "私用", "有給休暇"]

SCHEDULED_HOURS = 8.0
ABSENCE_RATE = 0.10


def gen_records(n, start_id):
    records = []
    dates = pd.date_range("2024-01-01", "2024-01-20", freq="D")
    for i in range(n):
        rid = start_id + i
        work_date = random.choice(dates)
        staff_type = random.choice(STAFF_TYPES_JP)
        department = random.choice(DEPARTMENTS_JP)
        staff_id = random.choice(STAFF_IDS)
        is_absent = 1 if random.random() < ABSENCE_RATE else 0
        if is_absent == 1:
            actual_hours = 0.0
            absence_reason = random.choice(ABSENCE_REASONS)
            overtime_hours = 0.0
        else:
            actual_hours = round(random.uniform(4.0, 12.0), 1)
            absence_reason = None
            diff = actual_hours - SCHEDULED_HOURS
            overtime_hours = round(diff, 1) if diff > 0 else 0.0
        records.append({
            "rid": rid,
            "work_date": work_date,
            "staff_type": staff_type,
            "department": department,
            "staff_id": staff_id,
            "scheduled_hours": SCHEDULED_HOURS,
            "actual_hours": actual_hours,
            "is_absent": is_absent,
            "absence_reason": absence_reason,
            "overtime_hours": overtime_hours,
        })
    return records


all_records = gen_records(480, 1)
rA = all_records[0:160]
rB = all_records[160:320]
rC = all_records[320:480]

# --- Style A (standard Japanese, date YYYY/MM/DD) ---
rows_a = []
for r in rA:
    d = r["work_date"].strftime("%Y/%m/%d")
    rid_str = "ATT-{:04d}".format(r["rid"])
    ar = "" if r["absence_reason"] is None else r["absence_reason"]
    rows_a.append({
        "勤務日": d,
        "記録ID": rid_str,
        "スタッフ種別": r["staff_type"],
        "診療科": r["department"],
        "スタッフID": r["staff_id"],
        "予定時間": r["scheduled_hours"],
        "実働時間": r["actual_hours"],
        "欠勤フラグ": r["is_absent"],
        "欠勤理由": ar,
        "残業時間": r["overtime_hours"],
    })
df_a = pd.DataFrame(rows_a)
df_a.to_csv(os.path.join(DATA_DIR, "attendance_styleA_202401.csv"), index=False, encoding="utf-8-sig")
print("[OK] StyleA: {} rows".format(len(df_a)))

# --- Style B (English, date YYYY-MM-DD) ---
rows_b = []
for r in rB:
    d = r["work_date"].strftime("%Y-%m-%d")
    rid_str = "ATT-{:04d}".format(r["rid"])
    ar = "" if r["absence_reason"] is None else r["absence_reason"]
    rows_b.append({
        "WorkDate": d,
        "RecordID": rid_str,
        "StaffType": r["staff_type"],
        "Department": r["department"],
        "StaffID": r["staff_id"],
        "ScheduledHours": r["scheduled_hours"],
        "ActualHours": r["actual_hours"],
        "IsAbsent": r["is_absent"],
        "AbsenceReason": ar,
        "OvertimeHours": r["overtime_hours"],
    })
df_b = pd.DataFrame(rows_b)
df_b.to_csv(os.path.join(DATA_DIR, "attendance_styleB_202401.csv"), index=False, encoding="utf-8-sig")
print("[OK] StyleB: {} rows".format(len(df_b)))

# --- Style C (variant Japanese, date YYYY/MM/DD) ---
rows_c = []
for r in rC:
    d = r["work_date"].strftime("%Y/%m/%d")
    rid_str = "ATT-{:04d}".format(r["rid"])
    ar = "" if r["absence_reason"] is None else r["absence_reason"]
    rows_c.append({
        "出勤日": d,
        "管理番号": rid_str,
        "職種区分": r["staff_type"],
        "所属科": r["department"],
        "職員ID": r["staff_id"],
        "所定時間": r["scheduled_hours"],
        "勤務時間": r["actual_hours"],
        "欠勤": r["is_absent"],
        "不在理由": ar,
        "残業": r["overtime_hours"],
    })
df_c = pd.DataFrame(rows_c)
df_c.to_csv(os.path.join(DATA_DIR, "attendance_styleC_202401.csv"), index=False, encoding="utf-8-sig")
print("[OK] StyleC: {} rows".format(len(df_c)))
print("[OK] Total: {} rows across 3 files".format(len(df_a) + len(df_b) + len(df_c)))

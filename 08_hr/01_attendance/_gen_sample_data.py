import pandas as pd
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
out = Path("C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/08_hr/01_attendance")

departments = ["営業部", "経理部", "人事部", "開発部", "総務部"]


def business_days(year=2024, month=1):
    days = []
    d = date(year, month, 1)
    while d.month == month:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


bdays = business_days()


def gen_employees(dept, n, style):
    employees = []
    for i in range(1, n+1):
        emp_id = f"EMP-{hash(dept+str(i)) % 900 + 100:03d}"
        emp_name = f"社員{i:03d}"
        employees.append((emp_id, emp_name))
    return employees


def gen_row(emp_id, emp_name, dept, work_date, style, is_heavy_worker=False):
    clock_in_h = random.randint(8, 9)
    clock_in_m = random.randint(0, 59) if clock_in_h == 8 else random.randint(0, 30)

    if is_heavy_worker and random.random() < 0.6:
        clock_out_h = random.randint(19, 22)
        clock_out_m = random.randint(0, 59)
    else:
        clock_out_h = random.randint(17, 19)
        clock_out_m = random.randint(0, 59)

    break_min = 60

    paid_leave = 1 if random.random() < 0.05 else 0
    if paid_leave:
        clock_in_h, clock_in_m = 9, 0
        clock_out_h, clock_out_m = 17, 30

    clock_in = f"{clock_in_h:02d}:{clock_in_m:02d}"
    clock_out = f"{clock_out_h:02d}:{clock_out_m:02d}"
    date_str = work_date.strftime("%Y/%m/%d")

    if style == "standard":
        return {
            "日付": date_str, "社員ID": emp_id, "氏名": emp_name,
            "部門": dept, "出勤時刻": clock_in, "退勤時刻": clock_out,
            "休憩(分)": break_min, "有給フラグ": paid_leave,
        }
    elif style == "english":
        return {
            "Date": date_str, "EmployeeID": emp_id, "Name": emp_name,
            "Department": dept, "ClockIn": clock_in, "ClockOut": clock_out,
            "BreakMinutes": break_min, "PaidLeave": paid_leave,
        }
    else:
        return {
            "勤務日": date_str, "社員番号": emp_id, "社員名": emp_name,
            "所属部門": dept, "出勤": clock_in, "退勤": clock_out,
            "休憩時間": break_min, "有給": paid_leave,
        }


files_config = [
    ("営業部",  "standard", "01_営業部_勤怠_202401.csv",   14),
    ("経理部",  "english",  "02_経理部_attendance_202401.csv", 10),
    ("人事部",  "variant",  "03_人事部_勤怠_202401.csv",   12),
    ("開発部",  "standard", "04_開発部_勤怠_202401.csv",   16),
    ("総務部",  "standard", "05_総務部_勤怠_202401.csv",   10),
]

for dept, style, filename, n_emp in files_config:
    employees = gen_employees(dept, n_emp, style)
    rows = []
    is_dev = (dept == "開発部")

    for emp_id, emp_name in employees:
        is_heavy = is_dev and random.random() < 0.5
        for d in bdays:
            if random.random() < 0.02:
                continue
            row = gen_row(emp_id, emp_name, dept, d, style, is_heavy_worker=is_heavy)
            rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(out / filename, index=False, encoding="utf-8-sig")
    print(f"Created {filename}: {len(df)} rows, {n_emp} employees, style={style}")

print("\nサンプルデータ生成完了（5部門）")

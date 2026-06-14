import pandas as pd
import numpy as np
import random
from datetime import date, timedelta, datetime
from pathlib import Path

rng = np.random.default_rng(42)
random.seed(42)
out = Path("C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/03_healthcare/01_patient_visit")

departments = ["内科", "外科", "小児科", "整形外科", "皮膚科"]
visit_routes = ["予約", "当日", "紹介状"]

# 診療科ごとの来院特性（平均来院数/日, 平均待ち時間分, ピーク時間帯）
dept_config = {
    "内科":    {"daily_n": (25, 35), "wait_mu": 45, "wait_sd": 20, "peak": (10, 11)},
    "外科":    {"daily_n": (10, 18), "wait_mu": 30, "wait_sd": 15, "peak": (9, 14)},
    "小児科":  {"daily_n": (20, 30), "wait_mu": 35, "wait_sd": 18, "peak": (10, 15)},
    "整形外科":{"daily_n": (15, 22), "wait_mu": 50, "wait_sd": 25, "peak": (9, 10)},
    "皮膚科":  {"daily_n": (12, 20), "wait_mu": 25, "wait_sd": 12, "peak": (14, 16)},
}

def all_days(year=2024, month=1):
    days = []
    d = date(year, month, 1)
    while d.month == month:
        days.append(d)
        d += timedelta(days=1)
    return days

month_days = all_days()

def gen_reception_time(d: date, dept: str) -> str:
    cfg = dept_config[dept]
    peak_start, peak_end = cfg["peak"]
    # 受付時間: 8:30〜17:00
    # ピーク時間帯は来院確率2倍
    hour_weights = []
    for h in range(9, 18):
        w = 2.0 if peak_start <= h <= peak_end else 1.0
        # 土日は来院数減少
        if d.weekday() >= 5:
            w *= 0.4
        hour_weights.append(w)
    hour = random.choices(range(9, 18), weights=hour_weights)[0]
    minute = random.randint(0, 59)
    return f"{hour:02d}:{minute:02d}"

def gen_rows(dept: str, col_style: str) -> list:
    cfg = dept_config[dept]
    rows = []
    patient_counter = 1000
    for d in month_days:
        # 土日は来院数40%
        factor = 0.4 if d.weekday() >= 5 else 1.0
        n_min, n_max = cfg["daily_n"]
        n = int(rng.integers(int(n_min * factor), int(n_max * factor) + 1))
        if n <= 0:
            continue
        for _ in range(n):
            patient_id = f"P-{patient_counter:05d}"
            patient_counter += random.randint(1, 5)
            reception = gen_reception_time(d, dept)
            wait_min = max(5, int(rng.normal(cfg["wait_mu"], cfg["wait_sd"])))
            # 10%確率で長時間待ち（60分超）
            if rng.random() < 0.10:
                wait_min = int(rng.uniform(70, 150))
            route = random.choices(visit_routes, weights=[0.6, 0.3, 0.1])[0]
            date_str = d.strftime("%Y/%m/%d")
            weekday = ["月", "火", "水", "木", "金", "土", "日"][d.weekday()]

            if col_style == "standard":
                rows.append({
                    "日付": date_str, "曜日": weekday,
                    "患者ID": patient_id, "診療科": dept,
                    "受付時刻": reception, "待ち時間(分)": wait_min,
                    "来院経路": route,
                })
            elif col_style == "english":
                rows.append({
                    "Date": date_str, "Weekday": weekday,
                    "PatientID": patient_id, "Department": dept,
                    "ReceptionTime": reception, "WaitMinutes": wait_min,
                    "VisitRoute": route,
                })
            else:  # variant
                rows.append({
                    "来院日": date_str, "曜日区分": weekday,
                    "受診番号": patient_id, "科": dept,
                    "チェックイン": reception, "待ち(分)": wait_min,
                    "経路": route,
                })
    return rows

files_config = [
    ("内科",    "standard", "01_内科_来院_202401.csv"),
    ("外科",    "english",  "02_外科_visit_202401.csv"),
    ("小児科",  "variant",  "03_小児科_来院_202401.csv"),
    ("整形外科","standard", "04_整形外科_来院_202401.csv"),
    ("皮膚科",  "standard", "05_皮膚科_来院_202401.csv"),
]

for dept, style, filename in files_config:
    rows = gen_rows(dept, style)
    df = pd.DataFrame(rows)
    df.to_csv(out / filename, index=False, encoding="utf-8-sig")
    print(f"Created {filename}: {len(df)} rows, style={style}")

print("\nサンプルデータ生成完了（5診療科）")

import pandas as pd
import numpy as np
import random
from pathlib import Path

rng = np.random.default_rng(42)
random.seed(42)
out = Path("C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/09_education/01_dropout_risk")

subjects    = ["数学", "英語", "物理", "国語", "情報"]
courses     = ["基礎コース", "応用コース", "上級コース"]
enroll_months = list(range(4, 13))  # 4月〜12月

def gen_student_row(sid: str, name: str, subject: str, course: str, enroll_month: int, risk_type: str, style: str) -> dict:
    if risk_type == "high":
        attendance    = float(rng.uniform(40, 70))
        midterm       = float(rng.uniform(20, 55))
        final         = float(rng.uniform(20, 50))
        assignment    = float(rng.uniform(30, 65))
        engagement    = int(rng.integers(1, 3))
    elif risk_type == "medium":
        attendance    = float(rng.uniform(65, 85))
        midterm       = float(rng.uniform(50, 75))
        final         = float(rng.uniform(45, 70))
        assignment    = float(rng.uniform(60, 85))
        engagement    = int(rng.integers(2, 4))
    else:  # low risk
        attendance    = float(rng.uniform(80, 100))
        midterm       = float(rng.uniform(65, 100))
        final         = float(rng.uniform(60, 100))
        assignment    = float(rng.uniform(75, 100))
        engagement    = int(rng.integers(3, 6))

    attendance    = round(min(100, attendance), 1)
    midterm       = round(min(100, midterm), 1)
    final_score   = round(min(100, final), 1)
    assignment    = round(min(100, assignment), 1)

    if style == "standard":
        return {
            "受講生ID": sid, "氏名": name, "科目名": subject,
            "出席率(%)": attendance, "中間テスト点数": midterm,
            "期末テスト点数": final_score, "課題提出率(%)": assignment,
            "参加スコア(1-5)": engagement, "入学月": enroll_month, "コース": course,
        }
    elif style == "english":
        return {
            "StudentID": sid, "StudentName": name, "Subject": subject,
            "AttendanceRate": attendance, "MidtermScore": midterm,
            "FinalScore": final_score, "AssignmentRate": assignment,
            "EngagementScore": engagement, "EnrollmentMonth": enroll_month, "Course": course,
        }
    else:
        return {
            "学生番号": sid, "名前": name, "科目": subject,
            "出席率": attendance, "中間点": midterm,
            "期末点": final_score, "提出率": assignment,
            "積極性": engagement, "入学月": enroll_month, "コース名": course,
        }

n_students = 200
risk_types = (["low"] * 80 + ["medium"] * 90 + ["high"] * 30)
random.shuffle(risk_types)

batches = [
    (range(1, 81),   "standard", "01_受講生データ_A班_202401.csv"),
    (range(81, 141), "english",  "02_student_data_B_202401.csv"),
    (range(141, 201),"variant",  "03_受講生データ_C班_202401.csv"),
]

student_names = [f"受講生{i:03d}" for i in range(1, 201)]

for id_range, style, filename in batches:
    rows = []
    for i in id_range:
        sid  = f"SID-{i:03d}"
        name = student_names[i-1]
        course       = random.choice(courses)
        enroll_month = random.choice(enroll_months)
        rtype        = risk_types[i-1]
        for subject in subjects:
            rows.append(gen_student_row(sid, name, subject, course, enroll_month, rtype, style))
    df = pd.DataFrame(rows)
    df.to_csv(out / filename, index=False, encoding="utf-8-sig")
    print(f"Created {filename}: {len(df)} rows, style={style}")

print("サンプルデータ生成完了（200受講生 × 5科目）")

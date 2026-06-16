import pandas as pd
import numpy as np
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
rng = np.random.default_rng(42)

OUT = Path("C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/09_education/02_instructor_workload/data")
OUT.mkdir(parents=True, exist_ok=True)

SPECIALTIES = ["IT・デジタル", "マネジメント", "コンプライアンス", "営業スキル", "語学"]
EMPLOYMENT_TYPES = ["正社員", "外部講師", "契約社員"]
# 雇用区分の比率: 50%, 30%, 20%
EMP_WEIGHTS = [0.50, 0.30, 0.20]

HOURLY_RATE_RANGES = {
    "正社員":   (2000, 3000),
    "外部講師": (5000, 8000),
    "契約社員": (3000, 4000),
}

COURSES = {
    "IT・デジタル":     ["Pythonプログラミング入門", "データ分析基礎", "DX推進セミナー", "クラウド活用研修", "セキュリティ基礎"],
    "マネジメント":     ["リーダーシップ研修", "目標管理(MBO)", "1on1面談スキル", "チームビルディング", "コーチング入門"],
    "コンプライアンス": ["個人情報保護法", "ハラスメント防止", "内部統制基礎", "情報セキュリティ研修", "コンプライアンス概論"],
    "営業スキル":       ["提案型営業", "ネゴシエーション", "プレゼンスキル", "顧客対応基礎", "営業データ分析"],
    "語学":             ["ビジネス英語", "TOEIC対策", "英語プレゼン", "グローバルコミュニケーション", "英文ビジネスライティング"],
}

VENUES = ["東京本社A会議室", "新宿研修センター", "大阪支社会議室", "名古屋オフィス", "オンライン(Zoom)", "オンライン(Teams)"]

# 20名の講師を固定生成
def make_instructors(n=20):
    instructors = []
    emp_list = random.choices(EMPLOYMENT_TYPES, weights=EMP_WEIGHTS, k=n)
    names = [
        "田中一郎", "佐藤花子", "鈴木次郎", "高橋三郎", "伊藤四郎",
        "渡辺美咲", "山本健太", "中村真理", "小林誠", "加藤由美",
        "吉田拓也", "山田早苗", "松本正樹", "井上彩", "木村隆二",
        "林奈央", "清水大輔", "山口遥", "斉藤哲也", "池田美穂",
    ]
    for i in range(n):
        emp = emp_list[i]
        low, high = HOURLY_RATE_RANGES[emp]
        rate = int(rng.integers(low, high + 1))
        specialty = random.choice(SPECIALTIES)
        instructors.append({
            "id": f"INS-{i+1:03d}",
            "name": names[i],
            "specialty": specialty,
            "employment_type": emp,
            "hourly_rate": rate,
        })
    return instructors

instructors = make_instructors(20)

def get_business_days(year=2024, month=1):
    days = []
    d = date(year, month, 1)
    while d.month == month:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days

bdays = get_business_days()


def gen_rows_style_a(instructors, bdays):
    """スタイルA: 標準日本語"""
    rows = []
    for d in bdays:
        # その日担当する講師をランダムに選ぶ(3〜8名)
        daily_instructors = random.sample(instructors, k=random.randint(3, 8))
        for inst in daily_instructors:
            n_slots = random.randint(1, 4)  # 1日最大4コマ
            courses_for_day = random.choices(COURSES[inst["specialty"]], k=n_slots)
            for course in courses_for_day:
                attendees = random.randint(5, 30)
                venue = random.choice(VENUES)
                rows.append({
                    "講師ID":    inst["id"],
                    "氏名":      inst["name"],
                    "専門分野":  inst["specialty"],
                    "雇用区分":  inst["employment_type"],
                    "実施日":    d.strftime("%Y/%m/%d"),
                    "コース名":  course,
                    "コマ数":    1,
                    "受講者数":  attendees,
                    "会場":      venue,
                    "時給単価":  inst["hourly_rate"],
                })
    return rows


def gen_rows_style_b(instructors, bdays):
    """スタイルB: 英語ヘッダー"""
    rows = []
    for d in bdays:
        daily_instructors = random.sample(instructors, k=random.randint(3, 8))
        for inst in daily_instructors:
            n_slots = random.randint(1, 4)
            courses_for_day = random.choices(COURSES[inst["specialty"]], k=n_slots)
            for course in courses_for_day:
                attendees = random.randint(5, 30)
                venue = random.choice(VENUES)
                rows.append({
                    "instructor_id":   inst["id"],
                    "name":            inst["name"],
                    "specialty":       inst["specialty"],
                    "employment_type": inst["employment_type"],
                    "session_date":    d.strftime("%Y-%m-%d"),
                    "course_name":     course,
                    "lesson_count":    1,
                    "attendee_count":  attendees,
                    "venue":           venue,
                    "hourly_rate":     inst["hourly_rate"],
                })
    return rows


def gen_rows_style_c(instructors, bdays):
    """スタイルC: 別表記"""
    rows = []
    for d in bdays:
        daily_instructors = random.sample(instructors, k=random.randint(3, 8))
        for inst in daily_instructors:
            n_slots = random.randint(1, 4)
            courses_for_day = random.choices(COURSES[inst["specialty"]], k=n_slots)
            for course in courses_for_day:
                attendees = random.randint(5, 30)
                venue = random.choice(VENUES)
                rows.append({
                    "社員番号":  inst["id"],
                    "講師名":    inst["name"],
                    "担当分野":  inst["specialty"],
                    "雇用形態":  inst["employment_type"],
                    "開催日":    d.strftime("%Y年%m月%d日"),
                    "研修名":    course,
                    "担当コマ":  1,
                    "参加人数":  attendees,
                    "開催場所":  venue,
                    "単価":      inst["hourly_rate"],
                })
    return rows


rows_a = gen_rows_style_a(instructors, bdays)
rows_b = gen_rows_style_b(instructors, bdays)
rows_c = gen_rows_style_c(instructors, bdays)

# 各スタイル170行以上になるまでデータを確保
# bdays=23日、3〜8名 × 1〜4コマ → 平均十分にある
# ただし保険として足りなければ追加
while len(rows_a) < 170:
    d = random.choice(bdays)
    inst = random.choice(instructors)
    course = random.choice(COURSES[inst["specialty"]])
    rows_a.append({
        "講師ID": inst["id"], "氏名": inst["name"], "専門分野": inst["specialty"],
        "雇用区分": inst["employment_type"], "実施日": d.strftime("%Y/%m/%d"),
        "コース名": course, "コマ数": 1, "受講者数": random.randint(5, 30),
        "会場": random.choice(VENUES), "時給単価": inst["hourly_rate"],
    })

while len(rows_b) < 170:
    d = random.choice(bdays)
    inst = random.choice(instructors)
    course = random.choice(COURSES[inst["specialty"]])
    rows_b.append({
        "instructor_id": inst["id"], "name": inst["name"], "specialty": inst["specialty"],
        "employment_type": inst["employment_type"], "session_date": d.strftime("%Y-%m-%d"),
        "course_name": course, "lesson_count": 1, "attendee_count": random.randint(5, 30),
        "venue": random.choice(VENUES), "hourly_rate": inst["hourly_rate"],
    })

while len(rows_c) < 170:
    d = random.choice(bdays)
    inst = random.choice(instructors)
    course = random.choice(COURSES[inst["specialty"]])
    rows_c.append({
        "社員番号": inst["id"], "講師名": inst["name"], "担当分野": inst["specialty"],
        "雇用形態": inst["employment_type"], "開催日": d.strftime("%Y年%m月%d日"),
        "研修名": course, "担当コマ": 1, "参加人数": random.randint(5, 30),
        "開催場所": random.choice(VENUES), "単価": inst["hourly_rate"],
    })

df_a = pd.DataFrame(rows_a)
df_b = pd.DataFrame(rows_b)
df_c = pd.DataFrame(rows_c)

df_a.to_csv(OUT / "01_instructor_schedule_styleA.csv", index=False, encoding="utf-8-sig")
df_b.to_csv(OUT / "02_instructor_schedule_styleB.csv", index=False, encoding="utf-8-sig")
df_c.to_csv(OUT / "03_instructor_schedule_styleC.csv", index=False, encoding="utf-8-sig")

total = len(df_a) + len(df_b) + len(df_c)
print(f"スタイルA: {len(df_a)} 行")
print(f"スタイルB: {len(df_b)} 行")
print(f"スタイルC: {len(df_c)} 行")
print(f"合計: {total} 行")
print("サンプルデータ生成完了")

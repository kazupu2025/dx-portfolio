import pandas as pd
import numpy as np
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
rng = np.random.default_rng(42)

BASE = Path(__file__).parent
OUT = BASE / "data"
OUT.mkdir(parents=True, exist_ok=True)

COURSES = [
    "Pythonプログラミング",
    "Excel基礎",
    "ビジネス英語",
    "プレゼン技術",
    "リーダーシップ",
]

LEARNER_TYPES = ["新入社員", "中堅社員", "管理職"]
LEARNER_WEIGHTS = [0.40, 0.40, 0.20]

STATUSES = ["修了", "受講中", "中途離脱"]
STATUS_WEIGHTS = [0.65, 0.25, 0.10]


def make_date(style: str) -> str:
    base = date(2024, 1, 1)
    d = base + timedelta(days=int(rng.integers(0, 31)))
    if style in ("A", "C"):
        return d.strftime("%Y/%m/%d")
    else:
        return d.strftime("%Y-%m-%d")


def make_score(status: str) -> int:
    if status == "修了":
        return int(rng.integers(60, 101))
    elif status == "受講中":
        return int(rng.integers(0, 81))
    else:
        return int(rng.integers(0, 51))


def make_hours(status: str) -> float:
    if status == "修了":
        return round(float(rng.uniform(8.0, 40.0)), 1)
    elif status == "受講中":
        return round(float(rng.uniform(2.0, 25.0)), 1)
    else:
        return round(float(rng.uniform(0.5, 10.0)), 1)


def gen_rows_style_a(n: int) -> list:
    rows = []
    for i in range(n):
        status = random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
        rows.append({
            "受講日":       make_date("A"),
            "受講番号":     f"ENR-A-{i+1:04d}",
            "講座名":       random.choice(COURSES),
            "受講者タイプ": random.choices(LEARNER_TYPES, weights=LEARNER_WEIGHTS, k=1)[0],
            "受講時間":     make_hours(status),
            "テストスコア": make_score(status),
            "ステータス":   status,
            "満足度":       int(rng.integers(1, 6)),
        })
    return rows


def gen_rows_style_b(n: int) -> list:
    rows = []
    for i in range(n):
        status = random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
        rows.append({
            "EnrollDate":  make_date("B"),
            "EnrollNo":    f"ENR-B-{i+1:04d}",
            "CourseName":  random.choice(COURSES),
            "LearnerType": random.choices(LEARNER_TYPES, weights=LEARNER_WEIGHTS, k=1)[0],
            "StudyHours":  make_hours(status),
            "TestScore":   make_score(status),
            "Status":      status,
            "Satisfaction": int(rng.integers(1, 6)),
        })
    return rows


def gen_rows_style_c(n: int) -> list:
    rows = []
    for i in range(n):
        status = random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
        rows.append({
            "日付":     make_date("C"),
            "管理番号": f"ENR-C-{i+1:04d}",
            "講座":     random.choice(COURSES),
            "受講区分": random.choices(LEARNER_TYPES, weights=LEARNER_WEIGHTS, k=1)[0],
            "学習時間": make_hours(status),
            "スコア":   make_score(status),
            "状況":     status,
            "評価":     int(rng.integers(1, 6)),
        })
    return rows


rows_a = gen_rows_style_a(140)
rows_b = gen_rows_style_b(140)
rows_c = gen_rows_style_c(140)

df_a = pd.DataFrame(rows_a)
df_b = pd.DataFrame(rows_b)
df_c = pd.DataFrame(rows_c)

df_a.to_csv(OUT / "01_enrollment_styleA.csv", index=False, encoding="utf-8-sig")
df_b.to_csv(OUT / "02_enrollment_styleB.csv", index=False, encoding="utf-8-sig")
df_c.to_csv(OUT / "03_enrollment_styleC.csv", index=False, encoding="utf-8-sig")

total = len(df_a) + len(df_b) + len(df_c)
print(f"スタイルA: {len(df_a)} 行")
print(f"スタイルB: {len(df_b)} 行")
print(f"スタイルC: {len(df_c)} 行")
print(f"合計: {total} 行")
print("サンプルデータ生成完了")

# _gen_sample_data.py — サンプルデータ生成スクリプト（C-36 顧客満足度）
# encoding: utf-8

import random
import csv
import os
from pathlib import Path

random.seed(42)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

SERVICE_TYPES = ["ITサポート", "コンサルティング", "保守", "導入支援", "研修"]
AGENTS = ["田中", "佐藤", "鈴木", "高橋", "伊藤"]

DATES_SLASH = [
    f"2024/{m:02d}/{d:02d}"
    for m in range(1, 13)
    for d in range(1, 29)
]
DATES_HYPHEN = [d.replace("/", "-") for d in DATES_SLASH]

random.shuffle(DATES_SLASH)
random.shuffle(DATES_HYPHEN)


def _rand_score(lo=1, hi=5):
    return random.randint(lo, hi)


def _rand_nps():
    return random.randint(0, 10)


def _customer_code(i):
    return f"C{i:04d}"


# ── スタイルA（標準日本語列名, YYYY/MM/DD）─────────────────────────────────
STYLE_A_ROWS = 140

with open(DATA_DIR / "satisfaction_styleA.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["回答日", "顧客コード", "サービス区分", "担当者",
                     "総合満足度", "対応速度", "品質", "コスパ", "推奨度"])
    for i in range(STYLE_A_ROWS):
        writer.writerow([
            DATES_SLASH[i % len(DATES_SLASH)],
            _customer_code(i + 1),
            random.choice(SERVICE_TYPES),
            random.choice(AGENTS),
            _rand_score(), _rand_score(), _rand_score(), _rand_score(),
            _rand_nps(),
        ])

# ── スタイルB（英語列名, YYYY-MM-DD）─────────────────────────────────────
STYLE_B_ROWS = 140

with open(DATA_DIR / "satisfaction_styleB.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["ResponseDate", "CustomerCode", "ServiceType", "Agent",
                     "OverallSat", "ResponseSpeed", "Quality", "CostPerf", "NPS"])
    for i in range(STYLE_B_ROWS):
        writer.writerow([
            DATES_HYPHEN[i % len(DATES_HYPHEN)],
            _customer_code(i + 141),
            random.choice(SERVICE_TYPES),
            random.choice(AGENTS),
            _rand_score(), _rand_score(), _rand_score(), _rand_score(),
            _rand_nps(),
        ])

# ── スタイルC（バリアント日本語列名, YYYY/MM/DD）──────────────────────────
STYLE_C_ROWS = 140

with open(DATA_DIR / "satisfaction_styleC.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["調査日", "顧客ID", "サービス種別", "対応者",
                     "総合評価", "速度評価", "品質評価", "費用対効果", "NPS推奨"])
    for i in range(STYLE_C_ROWS):
        writer.writerow([
            DATES_SLASH[i % len(DATES_SLASH)],
            _customer_code(i + 281),
            random.choice(SERVICE_TYPES),
            random.choice(AGENTS),
            _rand_score(), _rand_score(), _rand_score(), _rand_score(),
            _rand_nps(),
        ])

total = STYLE_A_ROWS + STYLE_B_ROWS + STYLE_C_ROWS
print(f"Sample data generated: {total} rows total (A={STYLE_A_ROWS}, B={STYLE_B_ROWS}, C={STYLE_C_ROWS})")
print(f"Output directory: {DATA_DIR}")

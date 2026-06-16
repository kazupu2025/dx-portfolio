"""
C-20: 飲食 x 人事・労務 -- アルバイトシフト・人件費集計パイプライン
サンプルデータ生成スクリプト

3店舗 x 20スタッフ x 25日(欠勤あり) = 各スタイル約500行
スタイルA: 標準日本語列名
スタイルB: 英語列名
スタイルC: 別表記列名
"""

import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

random.seed(42)
rng = np.random.default_rng(42)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

STORES = ["R001_新宿店", "R002_渋谷店", "R003_池袋店"]
EMPLOYMENT_TYPES = ["アルバイト", "パート", "社員"]
EMPLOYMENT_WEIGHTS = [0.70, 0.20, 0.10]

HOURLY_WAGE_RANGE = {
    "アルバイト": (1050, 1200),
    "パート": (1100, 1300),
    "社員": (1800, 2200),
}


def generate_staff(store_id: str, n: int = 20) -> list[dict]:
    """店舗スタッフマスタを生成"""
    staff = []
    emp_choices = random.choices(EMPLOYMENT_TYPES, weights=EMPLOYMENT_WEIGHTS, k=n)
    for i in range(n):
        store_code = store_id.split("_")[0]
        emp = emp_choices[i]
        lo, hi = HOURLY_WAGE_RANGE[emp]
        wage = random.randint(lo, hi)
        staff.append({
            "staff_id": f"{store_code}-S{i+1:02d}",
            "name": f"スタッフ{store_code}{i+1:02d}",
            "store_id": store_id,
            "employment_type": emp,
            "hourly_wage": wage,
        })
    return staff


def get_work_dates(year: int = 2024, month: int = 1) -> list[date]:
    """対象月の全日付を返す"""
    days = []
    d = date(year, month, 1)
    while d.month == month:
        days.append(d)
        d += timedelta(days=1)
    return days


def generate_shift(staff: dict, d: date) -> dict | None:
    """1スタッフ1日のシフトレコードを生成。欠勤は None を返す"""
    # 欠勤率: アルバイト20%, パート15%, 社員5%
    absence_rate = {"アルバイト": 0.20, "パート": 0.15, "社員": 0.05}
    if random.random() < absence_rate[staff["employment_type"]]:
        return None

    # 勤務開始: 社員は9-11時, アルバイト/パートは10-21時
    if staff["employment_type"] == "社員":
        start_hour = random.randint(9, 11)
    else:
        start_hour = random.randint(10, 21)

    start_min = random.choice([0, 30])

    # 実働時間: 3〜8時間
    work_hours = round(random.uniform(3.0, 8.0), 1)

    # 終業時刻
    total_minutes = start_hour * 60 + start_min + int(work_hours * 60)
    end_hour = total_minutes // 60
    end_min = total_minutes % 60

    # 休憩時間: 6時間超は45分, 8時間は60分
    if work_hours >= 8:
        break_minutes = 60
    elif work_hours >= 6:
        break_minutes = 45
    else:
        break_minutes = 0

    # 深夜区分(22時以降に退勤 or 在務中に22時をまたぐ場合)
    late_night = end_hour >= 22

    clock_in = f"{start_hour:02d}:{start_min:02d}"
    clock_out = f"{end_hour % 24:02d}:{end_min:02d}"

    return {
        "staff_id": staff["staff_id"],
        "name": staff["name"],
        "store_id": staff["store_id"],
        "employment_type": staff["employment_type"],
        "hourly_wage": staff["hourly_wage"],
        "work_date": d,
        "clock_in": clock_in,
        "clock_out": clock_out,
        "break_minutes": break_minutes,
        "work_hours": work_hours,
        "late_night": late_night,
    }


def to_style_a(rec: dict) -> dict:
    """スタイルA: 標準日本語列名"""
    return {
        "スタッフID": rec["staff_id"],
        "氏名": rec["name"],
        "店舗ID": rec["store_id"],
        "雇用区分": rec["employment_type"],
        "時給": rec["hourly_wage"],
        "勤務日": rec["work_date"].strftime("%Y/%m/%d"),
        "出勤時刻": rec["clock_in"],
        "退勤時刻": rec["clock_out"],
        "休憩分": rec["break_minutes"],
        "実働時間": rec["work_hours"],
        "深夜区分": rec["late_night"],
    }


def to_style_b(rec: dict) -> dict:
    """スタイルB: 英語列名"""
    return {
        "staff_id": rec["staff_id"],
        "name": rec["name"],
        "store_id": rec["store_id"],
        "employment_type": rec["employment_type"],
        "hourly_wage": rec["hourly_wage"],
        "work_date": rec["work_date"].strftime("%Y-%m-%d"),
        "clock_in": rec["clock_in"],
        "clock_out": rec["clock_out"],
        "break_minutes": rec["break_minutes"],
        "work_hours": rec["work_hours"],
        "late_night": rec["late_night"],
    }


def to_style_c(rec: dict) -> dict:
    """スタイルC: 別表記列名"""
    return {
        "社員番号": rec["staff_id"],
        "スタッフ名": rec["name"],
        "店番": rec["store_id"],
        "雇用形態": rec["employment_type"],
        "賃金": rec["hourly_wage"],
        "日付": rec["work_date"].strftime("%Y年%m月%d日"),
        "開始時刻": rec["clock_in"],
        "終了時刻": rec["clock_out"],
        "休憩時間": rec["break_minutes"],
        "勤務時間": rec["work_hours"],
        "深夜勤務": rec["late_night"],
    }


def main():
    work_dates = get_work_dates()

    # 店舗ごとにスタイルを割り当て
    configs = [
        ("R001_新宿店", "A", to_style_a, "shift_R001_202401.csv"),
        ("R002_渋谷店", "B", to_style_b, "shift_R002_202401.csv"),
        ("R003_池袋店", "C", to_style_c, "shift_R003_202401.csv"),
    ]

    for store_id, style, converter, filename in configs:
        staff_list = generate_staff(store_id, n=20)
        rows = []
        for d in work_dates:
            for staff in staff_list:
                shift = generate_shift(staff, d)
                if shift is not None:
                    rows.append(converter(shift))

        df = pd.DataFrame(rows)
        out_path = DATA_DIR / filename
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"Created {filename}: {len(df)} rows (style {style})")

    total = sum(
        len(pd.read_csv(DATA_DIR / cfg[3], encoding="utf-8-sig"))
        for cfg in configs
    )
    print(f"\n合計: {total} 行 (3店舗 x 20スタッフ x 約25日)")


if __name__ == "__main__":
    main()

"""
C-22 ドライバー勤怠・拘束時間管理パイプライン
サンプルデータ生成スクリプト
3スタイル（A/B/C）のCSVを data/ に出力する
"""
import random
import datetime
import os
import pandas as pd
from pathlib import Path

random.seed(42)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

OFFICES = ["東京営業所", "大阪営業所", "名古屋営業所"]
OPERATION_TYPES = ["長距離", "中距離", "市内配送"]

# ドライバー情報
DRIVERS = []
for i in range(1, 31):
    office = OFFICES[(i - 1) % 3]
    DRIVERS.append({
        "id": f"DRV{i:03d}",
        "name": f"ドライバー{i:02d}",
        "office": office,
    })

OPERATION_WEIGHTS = [0.25, 0.35, 0.40]  # 長距離・中距離・市内配送

# 日付: 2024年1月全日
DATES = [datetime.date(2024, 1, d) for d in range(1, 32)]


def gen_row(driver: dict) -> dict:
    op = random.choices(OPERATION_TYPES, weights=OPERATION_WEIGHTS, k=1)[0]
    date = random.choice(DATES)

    # 出庫時刻: 6〜10時
    depart_hour = random.randint(6, 10)
    depart_min = random.choice([0, 15, 30, 45])
    departure = datetime.datetime(2024, 1, date.day, depart_hour, depart_min)

    # 拘束時間の設定
    if op == "長距離":
        confinement_h = random.uniform(12.0, 14.5)
        break_h = round(random.uniform(1.0, 2.0), 1)
        dist = round(random.uniform(300, 600), 1)
    elif op == "中距離":
        confinement_h = random.uniform(9.0, 13.0)
        break_h = round(random.uniform(0.75, 1.5), 1)
        dist = round(random.uniform(100, 300), 1)
    else:  # 市内配送
        confinement_h = random.uniform(8.0, 11.0)
        break_h = round(random.uniform(0.5, 1.0), 1)
        dist = round(random.uniform(30, 100), 1)

    # 帰庫時刻
    return_minutes = int(confinement_h * 60)
    return_time = departure + datetime.timedelta(minutes=return_minutes)

    return {
        "driver_id": driver["id"],
        "name": driver["name"],
        "office": driver["office"],
        "work_date": date.strftime("%Y-%m-%d"),
        "departure_time": departure.strftime("%H:%M"),
        "return_time": return_time.strftime("%H:%M"),
        "break_hours": break_h,
        "distance_km": dist,
        "operation_type": op,
    }


def gen_rows(n: int) -> list:
    rows = []
    for _ in range(n):
        driver = random.choice(DRIVERS)
        rows.append(gen_row(driver))
    return rows


def gen_style_a(rows: list, start_idx: int = 1) -> pd.DataFrame:
    """スタイルA: 標準日本語列名"""
    records = []
    for i, r in enumerate(rows):
        records.append({
            "ドライバーID": r["driver_id"],
            "氏名": r["name"],
            "営業所": r["office"],
            "乗務日": r["work_date"],
            "出庫時刻": r["departure_time"],
            "帰庫時刻": r["return_time"],
            "休憩時間h": r["break_hours"],
            "走行距離km": r["distance_km"],
            "運行区分": r["operation_type"],
        })
    return pd.DataFrame(records)


def gen_style_b(rows: list, start_idx: int = 1) -> pd.DataFrame:
    """スタイルB: 英語列名"""
    records = []
    for i, r in enumerate(rows):
        records.append({
            "driver_id": r["driver_id"],
            "name": r["name"],
            "office": r["office"],
            "work_date": r["work_date"],
            "departure_time": r["departure_time"],
            "return_time": r["return_time"],
            "break_hours": r["break_hours"],
            "distance_km": r["distance_km"],
            "operation_type": r["operation_type"],
        })
    return pd.DataFrame(records)


def gen_style_c(rows: list, start_idx: int = 1) -> pd.DataFrame:
    """スタイルC: 別表記"""
    records = []
    for i, r in enumerate(rows):
        records.append({
            "社員番号": r["driver_id"],
            "運転者名": r["name"],
            "所属": r["office"],
            "乗務日付": r["work_date"],
            "出発時刻": r["departure_time"],
            "到着時刻": r["return_time"],
            "休憩h": r["break_hours"],
            "走行km": r["distance_km"],
            "運行種別": r["operation_type"],
        })
    return pd.DataFrame(records)


def main():
    n_each = 200
    all_rows = gen_rows(n_each * 3)

    rows_a = all_rows[:n_each]
    rows_b = all_rows[n_each: n_each * 2]
    rows_c = all_rows[n_each * 2: n_each * 3]

    df_a = gen_style_a(rows_a)
    df_b = gen_style_b(rows_b)
    df_c = gen_style_c(rows_c)

    path_a = DATA_DIR / "driver_202401_styleA.csv"
    path_b = DATA_DIR / "driver_202401_styleB.csv"
    path_c = DATA_DIR / "driver_202401_styleC.csv"

    df_a.to_csv(path_a, index=False, encoding="utf-8-sig")
    df_b.to_csv(path_b, index=False, encoding="utf-8-sig")
    df_c.to_csv(path_c, index=False, encoding="utf-8-sig")

    print(f"[OK] StyleA: {len(df_a)} rows -> {path_a}")
    print(f"[OK] StyleB: {len(df_b)} rows -> {path_b}")
    print(f"[OK] StyleC: {len(df_c)} rows -> {path_c}")
    print(f"[OK] Total : {len(df_a) + len(df_b) + len(df_c)} rows")


if __name__ == "__main__":
    main()

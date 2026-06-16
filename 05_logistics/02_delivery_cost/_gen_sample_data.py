"""
C-17 配送コスト分析パイプライン
サンプルデータ生成スクリプト
3スタイル（A/B/C）のCSVを data/ に出力する
"""
import random
import os
import pandas as pd
from pathlib import Path

random.seed(42)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

ROUTES = ["R01_東京-横浜", "R02_東京-埼玉", "R03_大阪-神戸", "R04_大阪-京都", "R05_名古屋-豊田"]
VEHICLES = ["2tトラック", "4tトラック", "10tトラック", "軽バン"]
STATUSES = ["完了", "遅延", "キャンセル"]
STATUS_WEIGHTS = [0.80, 0.15, 0.05]

VEHICLE_DISTANCE_RANGE = {
    "2tトラック": (30, 120),
    "4tトラック": (40, 150),
    "10tトラック": (50, 200),
    "軽バン": (10, 60),
}
VEHICLE_FUEL_COST_PER_KM = {
    "2tトラック": (18, 30),
    "4tトラック": (25, 40),
    "10tトラック": (40, 65),
    "軽バン": (8, 15),
}
VEHICLE_DRIVER_COST = {
    "2tトラック": (15000, 25000),
    "4tトラック": (18000, 30000),
    "10tトラック": (22000, 38000),
    "軽バン": (10000, 18000),
}
VEHICLE_WEIGHT_RANGE = {
    "2tトラック": (500, 2000),
    "4tトラック": (1000, 4000),
    "10tトラック": (3000, 10000),
    "軽バン": (50, 500),
}


def gen_row(idx: int):
    vehicle = random.choice(VEHICLES)
    route = random.choice(ROUTES)
    distance = round(random.uniform(*VEHICLE_DISTANCE_RANGE[vehicle]), 1)
    fpc = random.uniform(*VEHICLE_FUEL_COST_PER_KM[vehicle])
    fuel_cost = round(distance * fpc)
    toll_cost = round(random.uniform(500, 3000) if random.random() < 0.7 else 0)
    driver_cost = round(random.uniform(*VEHICLE_DRIVER_COST[vehicle]))
    cargo_weight = round(random.uniform(*VEHICLE_WEIGHT_RANGE[vehicle]), 1)
    delivery_count = random.randint(1, 30)
    status = random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
    date_offset = random.randint(0, 30)
    import datetime
    date = (datetime.date(2024, 1, 1) + datetime.timedelta(days=date_offset)).strftime("%Y-%m-%d")
    return {
        "vehicle": vehicle,
        "route": route,
        "distance": distance,
        "fuel_cost": fuel_cost,
        "toll_cost": toll_cost,
        "driver_cost": driver_cost,
        "cargo_weight": cargo_weight,
        "delivery_count": delivery_count,
        "status": status,
        "date": date,
    }


def gen_style_a(rows, start_idx=1):
    """スタイルA: 標準日本語列名"""
    records = []
    for i, r in enumerate(rows):
        records.append({
            "配送ID": f"A-{start_idx + i:04d}",
            "日付": r["date"],
            "ルートID": r["route"],
            "車種": r["vehicle"],
            "距離km": r["distance"],
            "燃料費": r["fuel_cost"],
            "高速代": r["toll_cost"],
            "ドライバー人件費": r["driver_cost"],
            "積載重量kg": r["cargo_weight"],
            "配送件数": r["delivery_count"],
            "配送ステータス": r["status"],
        })
    return pd.DataFrame(records)


def gen_style_b(rows, start_idx=1):
    """スタイルB: 英語列名"""
    records = []
    for i, r in enumerate(rows):
        records.append({
            "delivery_id": f"B-{start_idx + i:04d}",
            "date": r["date"],
            "route_id": r["route"],
            "vehicle_type": r["vehicle"],
            "distance_km": r["distance"],
            "fuel_cost": r["fuel_cost"],
            "toll_cost": r["toll_cost"],
            "driver_cost": r["driver_cost"],
            "cargo_weight_kg": r["cargo_weight"],
            "delivery_count": r["delivery_count"],
            "status": r["status"],
        })
    return pd.DataFrame(records)


def gen_style_c(rows, start_idx=1):
    """スタイルC: 別表記（混在）"""
    records = []
    for i, r in enumerate(rows):
        records.append({
            "伝票番号": f"C-{start_idx + i:04d}",
            "集計日": r["date"],
            "路線": r["route"],
            "車両種別": r["vehicle"],
            "走行距離": r["distance"],
            "燃費費用": r["fuel_cost"],
            "道路料金": r["toll_cost"],
            "人件費": r["driver_cost"],
            "荷重": r["cargo_weight"],
            "件数": r["delivery_count"],
            "状態": r["status"],
        })
    return pd.DataFrame(records)


def main():
    all_rows = [gen_row(i) for i in range(600)]
    n_a, n_b, n_c = 200, 200, 200

    df_a = gen_style_a(all_rows[:n_a], start_idx=1)
    df_b = gen_style_b(all_rows[n_a:n_a + n_b], start_idx=1)
    df_c = gen_style_c(all_rows[n_a + n_b:n_a + n_b + n_c], start_idx=1)

    path_a = DATA_DIR / "delivery_202401_styleA.csv"
    path_b = DATA_DIR / "delivery_202401_styleB.csv"
    path_c = DATA_DIR / "delivery_202401_styleC.csv"

    df_a.to_csv(path_a, index=False, encoding="utf-8-sig")
    df_b.to_csv(path_b, index=False, encoding="utf-8-sig")
    df_c.to_csv(path_c, index=False, encoding="utf-8-sig")

    print(f"[OK] StyleA: {len(df_a)} rows -> {path_a}")
    print(f"[OK] StyleB: {len(df_b)} rows -> {path_b}")
    print(f"[OK] StyleC: {len(df_c)} rows -> {path_c}")
    print(f"[OK] Total: {len(df_a) + len(df_b) + len(df_c)} rows")


if __name__ == "__main__":
    main()

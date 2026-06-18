# -*- coding: utf-8 -*-
"""サンプルデータ生成スクリプト - 3スタイルのCSVを data/ に生成 (各160件、合計480件)"""
import os
import random
import pandas as pd
import numpy as np
from pathlib import Path

random.seed(42)
np.random.seed(42)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DELIVERY_TYPES = ["同日配送", "翌日配送", "翌々日配送", "大型配送"]
AREAS = ["関東", "関西", "東海", "九州", "東北"]
VEHICLE_TYPES = ["軽バン", "2トン", "4トン"]
DATES = pd.date_range("2024-01-01", "2024-01-20")

ROWS_PER_STYLE = 160
TOTAL_ROWS = ROWS_PER_STYLE * 3


def gen_all_rows():
    rows = []
    for i in range(TOTAL_ROWS):
        delivery_id = f"DLV-{i+1:04d}"
        date = random.choice(DATES)
        delivery_type = random.choice(DELIVERY_TYPES)
        area = random.choice(AREAS)
        vehicle_type = random.choice(VEHICLE_TYPES)
        delivery_charge = random.randint(1000, 15000)
        fuel_cost = random.randint(200, 3000)
        driver_cost = random.randint(3000, 8000)
        other_cost = random.randint(500, 2000)
        distance_km = random.randint(10, 200)
        rows.append({
            "date": date,
            "delivery_id": delivery_id,
            "delivery_type": delivery_type,
            "area": area,
            "vehicle_type": vehicle_type,
            "delivery_charge": delivery_charge,
            "fuel_cost": fuel_cost,
            "driver_cost": driver_cost,
            "other_cost": other_cost,
            "distance_km": distance_km,
        })
    return rows


rows = gen_all_rows()
rows_a = rows[:ROWS_PER_STYLE]
rows_b = rows[ROWS_PER_STYLE:ROWS_PER_STYLE * 2]
rows_c = rows[ROWS_PER_STYLE * 2:]

# Style A (standard Japanese, date=YYYY/MM/DD)
df_a = pd.DataFrame([{
    "配送日": r["date"].strftime("%Y/%m/%d"),
    "配送ID": r["delivery_id"],
    "配送区分": r["delivery_type"],
    "エリア": r["area"],
    "車両タイプ": r["vehicle_type"],
    "配送料": r["delivery_charge"],
    "燃料費": r["fuel_cost"],
    "人件費": r["driver_cost"],
    "その他費用": r["other_cost"],
    "距離(km)": r["distance_km"],
} for r in rows_a])

# Style B (English, date=YYYY-MM-DD)
df_b = pd.DataFrame([{
    "DeliveryDate": r["date"].strftime("%Y-%m-%d"),
    "DeliveryID": r["delivery_id"],
    "DeliveryType": r["delivery_type"],
    "Area": r["area"],
    "VehicleType": r["vehicle_type"],
    "DeliveryCharge": r["delivery_charge"],
    "FuelCost": r["fuel_cost"],
    "DriverCost": r["driver_cost"],
    "OtherCost": r["other_cost"],
    "DistanceKm": r["distance_km"],
} for r in rows_b])

# Style C (variant Japanese, date=YYYY/MM/DD)
df_c = pd.DataFrame([{
    "日付": r["date"].strftime("%Y/%m/%d"),
    "便番号": r["delivery_id"],
    "配送タイプ": r["delivery_type"],
    "配送地域": r["area"],
    "車種": r["vehicle_type"],
    "運賃": r["delivery_charge"],
    "ガソリン代": r["fuel_cost"],
    "運転手費用": r["driver_cost"],
    "雑費": r["other_cost"],
    "走行距離": r["distance_km"],
} for r in rows_c])

df_a.to_csv(DATA_DIR / "delivery_cost_styleA_202401.csv", index=False, encoding="utf-8-sig")
df_b.to_csv(DATA_DIR / "delivery_cost_styleB_202401.csv", index=False, encoding="utf-8-sig")
df_c.to_csv(DATA_DIR / "delivery_cost_styleC_202401.csv", index=False, encoding="utf-8-sig")

print(f"[OK] 生成完了: A={len(df_a)}行, B={len(df_b)}行, C={len(df_c)}行, 合計={len(df_a)+len(df_b)+len(df_c)}行")

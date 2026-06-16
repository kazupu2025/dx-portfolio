# -*- coding: utf-8 -*-
"""
サンプルデータ生成スクリプト
3スタイルのCSVを data/ フォルダに生成する
"""
import random
import csv
import os
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

ROUTES = [f"R{i:02d}" for i in range(1, 11)]
AREAS = ["東京", "大阪", "名古屋", "福岡", "札幌"]
VEHICLE_TYPES = ["軽バン", "2tトラック", "4tトラック"]

START_DATE = date(2024, 1, 1)
END_DATE = date(2024, 1, 31)


def random_date_range(fmt="%Y/%m/%d"):
    delta = (END_DATE - START_DATE).days
    d = START_DATE + timedelta(days=random.randint(0, delta))
    return d.strftime(fmt)


def random_route_data():
    route_id = random.choice(ROUTES)
    area = random.choice(AREAS)
    vehicle = random.choice(VEHICLE_TYPES)

    if vehicle == "軽バン":
        distance = round(random.uniform(20, 80), 1)
        duration = int(random.uniform(60, 180))
        fuel = round(random.uniform(800, 2500), 0)
        deliveries = random.randint(5, 20)
    elif vehicle == "2tトラック":
        distance = round(random.uniform(50, 150), 1)
        duration = int(random.uniform(120, 360))
        fuel = round(random.uniform(2000, 6000), 0)
        deliveries = random.randint(10, 40)
    else:  # 4tトラック
        distance = round(random.uniform(80, 200), 1)
        duration = int(random.uniform(180, 480))
        fuel = round(random.uniform(4000, 12000), 0)
        deliveries = random.randint(15, 60)

    delay_flag = 1 if random.random() < 0.20 else 0
    return route_id, area, vehicle, distance, duration, fuel, deliveries, delay_flag


# スタイルA: 標準日本語列名、日付フォーマット YYYY/MM/DD
def gen_style_a(n=140):
    filepath = DATA_DIR / "routes_styleA.csv"
    with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "運行日", "ルートID", "エリア", "車両タイプ",
            "走行距離km", "所要時間分", "燃料費", "配送件数", "遅延フラグ"
        ])
        for _ in range(n):
            route_id, area, vehicle, distance, duration, fuel, deliveries, delay = random_route_data()
            writer.writerow([
                random_date_range("%Y/%m/%d"),
                route_id, area, vehicle,
                distance, duration, fuel, deliveries, delay
            ])
    print(f"[GEN] スタイルA: {n}行 -> {filepath}")


# スタイルB: 英語列名、日付フォーマット YYYY-MM-DD
def gen_style_b(n=140):
    filepath = DATA_DIR / "routes_styleB.csv"
    with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Date", "RouteID", "Area", "VehicleType",
            "DistanceKm", "DurationMin", "FuelCost", "DeliveryCount", "DelayFlag"
        ])
        for _ in range(n):
            route_id, area, vehicle, distance, duration, fuel, deliveries, delay = random_route_data()
            writer.writerow([
                random_date_range("%Y-%m-%d"),
                route_id, area, vehicle,
                distance, duration, fuel, deliveries, delay
            ])
    print(f"[GEN] スタイルB: {n}行 -> {filepath}")


# スタイルC: バリアント日本語列名、日付フォーマット YYYY/MM/DD
def gen_style_c(n=140):
    filepath = DATA_DIR / "routes_styleC.csv"
    with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "日付", "路線CD", "担当エリア", "車種",
            "走行km", "所要分", "燃油費", "件数", "遅延"
        ])
        for _ in range(n):
            route_id, area, vehicle, distance, duration, fuel, deliveries, delay = random_route_data()
            writer.writerow([
                random_date_range("%Y/%m/%d"),
                route_id, area, vehicle,
                distance, duration, fuel, deliveries, delay
            ])
    print(f"[GEN] スタイルC: {n}行 -> {filepath}")


if __name__ == "__main__":
    gen_style_a(140)
    gen_style_b(140)
    gen_style_c(140)
    print("[GEN] サンプルデータ生成完了（合計420行）")

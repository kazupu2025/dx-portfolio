# -*- coding: utf-8 -*-
"""データクレンジング: 3スタイルCSVを統一フォーマットに変換"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COLUMN_MAP = {
    # delivery_date
    "配送日": "delivery_date", "DeliveryDate": "delivery_date", "日付": "delivery_date",
    # delivery_id
    "配送ID": "delivery_id", "DeliveryID": "delivery_id", "便番号": "delivery_id",
    # delivery_type
    "配送区分": "delivery_type", "DeliveryType": "delivery_type", "配送タイプ": "delivery_type",
    # area
    "エリア": "area", "Area": "area", "配送地域": "area",
    # vehicle_type
    "車両タイプ": "vehicle_type", "VehicleType": "vehicle_type", "車種": "vehicle_type",
    # delivery_charge
    "配送料": "delivery_charge", "DeliveryCharge": "delivery_charge", "運賃": "delivery_charge",
    # fuel_cost
    "燃料費": "fuel_cost", "FuelCost": "fuel_cost", "ガソリン代": "fuel_cost",
    # driver_cost
    "人件費": "driver_cost", "DriverCost": "driver_cost", "運転手費用": "driver_cost",
    # other_cost
    "その他費用": "other_cost", "OtherCost": "other_cost", "雑費": "other_cost",
    # distance_km
    "距離(km)": "distance_km", "DistanceKm": "distance_km", "走行距離": "distance_km",
}

NUMERIC_COLS = ["delivery_charge", "fuel_cost", "driver_cost", "other_cost", "distance_km"]

CANONICAL_COLS = [
    "delivery_date", "delivery_id", "delivery_type", "area", "vehicle_type",
    "delivery_charge", "fuel_cost", "driver_cost", "other_cost", "distance_km",
    "total_cost", "gross_profit", "profit_margin", "cost_per_km",
    "margin_grade", "source_file",
]

dfs = []
for csv_file in sorted(DATA_DIR.glob("*.csv")):
    df = pd.read_csv(csv_file, encoding="utf-8-sig")
    df = df.rename(columns=COLUMN_MAP)
    df["source_file"] = csv_file.name
    dfs.append(df)

merged = pd.concat(dfs, ignore_index=True)

# Normalize date to YYYY-MM-DD
merged["delivery_date"] = merged["delivery_date"].astype(str).str.replace("/", "-", regex=False)
merged["delivery_date"] = pd.to_datetime(
    merged["delivery_date"], errors="coerce", format="%Y-%m-%d"
).dt.strftime("%Y-%m-%d")

# Coerce numeric columns
for col in NUMERIC_COLS:
    if col in merged.columns:
        merged[col] = pd.to_numeric(merged[col], errors="coerce")
        merged[col] = merged[col].fillna(merged[col].median())

# Derived columns
merged["total_cost"] = merged["fuel_cost"] + merged["driver_cost"] + merged["other_cost"]

merged["gross_profit"] = merged["delivery_charge"] - merged["total_cost"]

merged["profit_margin"] = np.where(
    merged["delivery_charge"] > 0,
    merged["gross_profit"] / merged["delivery_charge"],
    np.nan,
)

merged["cost_per_km"] = np.where(
    merged["distance_km"] > 0,
    merged["total_cost"] / merged["distance_km"],
    np.nan,
)


def calc_margin_grade(pm):
    if pd.isna(pm):
        return "低利益"
    if pm >= 0.3:
        return "高利益"
    elif pm >= 0.1:
        return "普通"
    else:
        return "低利益"


merged["margin_grade"] = merged["profit_margin"].apply(calc_margin_grade)

out_cols = [c for c in CANONICAL_COLS if c in merged.columns]
out_path = OUTPUT_DIR / "cleaned_deliveries_202401.csv"
merged[out_cols].to_csv(out_path, index=False, encoding="utf-8-sig")
print(f"[OK] クレンジング完了: {len(merged)}行 -> {out_path}")

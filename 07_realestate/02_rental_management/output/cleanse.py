"""
B-14 賃貸物件管理 - データクレンジング
入力: ../01_*.csv ~ ../05_*.csv (3スタイル混在)
出力: cleaned_rental_202401.csv
"""
import pandas as pd
import numpy as np
import yaml
import logging
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
OUT = Path(__file__).parent

logging.basicConfig(
    filename=OUT / "cleanse.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8",
)

COLUMN_MAP = {
    "物件ID": "property_id", "PropertyID": "property_id", "物件番号": "property_id",
    "物件名": "property_name", "PropertyName": "property_name", "物件名称": "property_name",
    "エリア": "area", "Area": "area", "地域": "area",
    "物件タイプ": "property_type", "PropertyType": "property_type", "タイプ": "property_type",
    "賃料(円)": "rent", "Rent": "rent", "月額賃料": "rent",
    "管理費(円)": "management_fee", "ManagementFee": "management_fee", "管理費": "management_fee",
    "入居状況": "occupancy_status", "OccupancyStatus": "occupancy_status", "状態": "occupancy_status",
    "入居開始日": "move_in_date", "MoveInDate": "move_in_date", "入居日": "move_in_date",
    "退去日": "move_out_date", "MoveOutDate": "move_out_date",
    "管理コスト(円)": "management_cost", "ManagementCost": "management_cost", "管理費用": "management_cost",
    "修繕費(円)": "repair_cost", "RepairCost": "repair_cost", "修繕費用": "repair_cost",
}

STATUS_MAP = {
    "入居中": "入居中", "Occupied": "入居中", "居住中": "入居中",
    "空室":   "空室",   "Vacant":   "空室",   "空き":   "空室",
    "募集中": "募集中", "ForRent":  "募集中", "募集":   "募集中",
}

KEEP_COLS = [
    "property_id", "property_name", "area", "property_type",
    "rent", "management_fee", "occupancy_status",
    "move_in_date", "move_out_date",
    "management_cost", "repair_cost",
    "is_vacant", "monthly_revenue", "total_cost", "net_income",
    "source_file",
]

def load_cfg():
    with open(BASE / "config.yml", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_csvs():
    frames = []
    for csv in sorted(BASE.glob("*.csv")):
        df = pd.read_csv(csv, encoding="utf-8-sig", dtype=str)
        df["source_file"] = csv.name
        # rename per-file before concat to avoid duplicate column names
        df = df.rename(columns={c: COLUMN_MAP[c] for c in df.columns if c in COLUMN_MAP})
        # keep only known canonical columns + source_file
        keep = [c for c in df.columns if c in set(COLUMN_MAP.values()) or c == "source_file"]
        df = df[keep]
        frames.append(df)
        logging.info(f"Loaded {csv.name}: {len(df)} rows")
    return pd.concat(frames, ignore_index=True)

def rename_columns(df):
    # already renamed per-file in load_csvs; this is a no-op pass
    return df

def normalize(df):
    # occupancy_status
    df["occupancy_status"] = df["occupancy_status"].replace(STATUS_MAP)

    # numeric cols
    for col in ["rent", "management_fee", "management_cost", "repair_cost"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).clip(lower=0)

    # derived columns
    df["is_vacant"] = df["occupancy_status"].isin(["空室", "募集中"]).astype(int)
    df["monthly_revenue"] = np.where(
        df["is_vacant"] == 0,
        df["rent"] + df["management_fee"],
        0
    )
    df["total_cost"] = df["management_cost"] + df["repair_cost"]
    df["net_income"] = df["monthly_revenue"] - df["total_cost"]

    # fill optional text cols
    for col in ["move_in_date", "move_out_date"]:
        if col in df.columns:
            df[col] = df[col].fillna("")
        else:
            df[col] = ""

    return df

def main():
    cfg = load_cfg()
    df = load_csvs()
    df = rename_columns(df)
    df = normalize(df)

    # keep only required cols
    extra = [c for c in df.columns if c not in KEEP_COLS]
    if extra:
        logging.info(f"Dropping extra cols: {extra}")
        df = df.drop(columns=extra)

    # add missing cols
    for col in KEEP_COLS:
        if col not in df.columns:
            df[col] = None
    df = df[KEEP_COLS]

    out_path = OUT / "cleaned_rental_202401.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    logging.info(f"Saved {out_path}: {len(df)} rows")
    print(f"Cleansed {len(df)} rows -> {out_path}")

if __name__ == "__main__":
    main()

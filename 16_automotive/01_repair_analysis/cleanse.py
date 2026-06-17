# -*- coding: utf-8 -*-
import os
import glob
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CANONICAL_COLS = [
    "order_date", "order_id", "shop_name", "work_type", "tech_id",
    "estimated_days", "actual_days", "labor_cost", "parts_cost", "status",
    "total_cost", "delay_days", "is_delayed", "is_returned",
    "efficiency_flag", "source_file",
]

COLUMN_MAP_A = {
    "受付日": "order_date",
    "依頼番号": "order_id",
    "店舗名": "shop_name",
    "作業区分": "work_type",
    "担当技術者": "tech_id",
    "予定日数": "estimated_days",
    "実績日数": "actual_days",
    "工賃": "labor_cost",
    "部品代": "parts_cost",
    "ステータス": "status",
}

COLUMN_MAP_B = {
    "OrderDate": "order_date",
    "OrderID": "order_id",
    "ShopName": "shop_name",
    "WorkType": "work_type",
    "TechID": "tech_id",
    "EstimatedDays": "estimated_days",
    "ActualDays": "actual_days",
    "LaborCost": "labor_cost",
    "PartsCost": "parts_cost",
    "Status": "status",
}

COLUMN_MAP_C = {
    "入庫日": "order_date",
    "作業番号": "order_id",
    "工場名": "shop_name",
    "整備種別": "work_type",
    "技術者ID": "tech_id",
    "見込み日数": "estimated_days",
    "完了日数": "actual_days",
    "技術料": "labor_cost",
    "部品費": "parts_cost",
    "進捗": "status",
}

STATUS_EN_TO_JP = {
    "Completed": "完了",
    "InProgress": "作業中",
    "Returned": "再入庫",
}

ALL_MAPS = [COLUMN_MAP_A, COLUMN_MAP_B, COLUMN_MAP_C]


def detect_and_map(df, source_file):
    cols = set(df.columns)
    for cmap in ALL_MAPS:
        if set(cmap.keys()).issubset(cols):
            df = df.rename(columns=cmap)
            break
    else:
        print(f"[WARN] Unknown column style in {source_file}, attempting best-effort mapping")
    df["source_file"] = os.path.basename(source_file)
    return df


def normalize(df):
    # date normalization
    df["order_date"] = (
        df["order_date"]
        .astype(str)
        .str.replace("/", "-")
    )
    df["order_date"] = pd.to_datetime(df["order_date"], format="%Y-%m-%d", errors="coerce").dt.strftime("%Y-%m-%d")

    # numeric conversion
    for col in ["estimated_days", "actual_days", "labor_cost", "parts_cost"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # English status -> Japanese
    df["status"] = df["status"].replace(STATUS_EN_TO_JP)

    # derived columns
    df["total_cost"] = df["labor_cost"] + df["parts_cost"]
    df["delay_days"] = df["actual_days"] - df["estimated_days"]
    df["is_delayed"] = (df["delay_days"] > 0).astype(int)
    df["is_returned"] = (df["status"] == "再入庫").astype(int)
    df["efficiency_flag"] = df["delay_days"].apply(lambda x: "効率的" if x <= 0 else "遅延")

    return df


def main():
    csv_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.csv")))
    if not csv_files:
        print("[FAIL] No CSV files found in data/")
        return

    frames = []
    for fpath in csv_files:
        df = pd.read_csv(fpath, encoding="utf-8-sig")
        df = detect_and_map(df, fpath)
        df = normalize(df)
        frames.append(df)
        print(f"[OK] Processed {os.path.basename(fpath)}: {len(df)} rows")

    combined = pd.concat(frames, ignore_index=True)

    # Output only canonical columns
    combined = combined[CANONICAL_COLS]

    out_path = os.path.join(OUTPUT_DIR, "cleaned_orders_202401.csv")
    combined.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[OK] Saved {len(combined)} rows -> {out_path}")


if __name__ == "__main__":
    main()

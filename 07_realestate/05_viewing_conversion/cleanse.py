# -*- coding: utf-8 -*-
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CANONICAL_COLS = [
    "visit_date",
    "visit_id",
    "property_type",
    "area",
    "staff_id",
    "asking_price",
    "visit_count_cumulative",
    "days_to_contract",
    "is_contracted",
    "price_tier",
    "conversion_speed",
    "source_file",
]

COLUMN_MAP = {
    # StyleA
    "内見日": "visit_date",
    "内見ID": "visit_id",
    "物件タイプ": "property_type",
    "エリア": "area",
    "担当者ID": "staff_id",
    "物件価格(万円)": "asking_price",
    "累計内見数": "visit_count_cumulative",
    "成約日数": "days_to_contract",
    "成約フラグ": "is_contracted",
    # StyleB
    "VisitDate": "visit_date",
    "VisitID": "visit_id",
    "PropertyType": "property_type",
    "Area": "area",
    "StaffID": "staff_id",
    "AskingPrice": "asking_price",
    "VisitCountCumulative": "visit_count_cumulative",
    "DaysToContract": "days_to_contract",
    "IsContracted": "is_contracted",
    # StyleC
    "見学日": "visit_date",
    "見学番号": "visit_id",
    "部屋タイプ": "property_type",
    "地域": "area",
    "担当ID": "staff_id",
    "価格": "asking_price",
    "見学累計回数": "visit_count_cumulative",
    "成約所要日": "days_to_contract",
    "成約": "is_contracted",
}


def normalize_date(series):
    s = series.astype(str).str.replace("/", "-", regex=False)
    return pd.to_datetime(s, format="%Y-%m-%d").dt.strftime("%Y-%m-%d")


def add_derived_cols(df):
    df["asking_price"] = pd.to_numeric(df["asking_price"], errors="coerce")
    df["visit_count_cumulative"] = pd.to_numeric(df["visit_count_cumulative"], errors="coerce")
    df["days_to_contract"] = pd.to_numeric(df["days_to_contract"], errors="coerce")
    df["is_contracted"] = pd.to_numeric(df["is_contracted"], errors="coerce").astype("Int64")

    df["price_tier"] = df["asking_price"].apply(
        lambda x: "高価格帯" if x >= 5000 else ("中価格帯" if x >= 3000 else "低価格帯")
    )

    def calc_speed(row):
        if row["is_contracted"] == 1 and row["days_to_contract"] <= 14:
            return "早期成約"
        elif row["is_contracted"] == 1:
            return "通常成約"
        else:
            return "未成約"

    df["conversion_speed"] = df.apply(calc_speed, axis=1)
    return df


def load_and_unify(filepath):
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    df = df.rename(columns=COLUMN_MAP)
    df["visit_date"] = normalize_date(df["visit_date"])
    df["source_file"] = os.path.basename(filepath)
    df = add_derived_cols(df)
    return df[CANONICAL_COLS]


files = [
    os.path.join(DATA_DIR, "visits_styleA.csv"),
    os.path.join(DATA_DIR, "visits_styleB.csv"),
    os.path.join(DATA_DIR, "visits_styleC.csv"),
]

dfs = []
for f in files:
    df = load_and_unify(f)
    dfs.append(df)
    print("[OK] Loaded {} ({} rows)".format(os.path.basename(f), len(df)))

combined = pd.concat(dfs, ignore_index=True)
out_path = os.path.join(OUTPUT_DIR, "cleaned_visits_202401.csv")
combined.to_csv(out_path, index=False, encoding="utf-8-sig")
print("[OK] Output: {} ({} rows)".format(out_path, len(combined)))

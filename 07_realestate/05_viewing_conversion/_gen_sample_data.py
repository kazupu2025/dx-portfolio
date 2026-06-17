# -*- coding: utf-8 -*-
import random
import numpy as np
import pandas as pd
import os

random.seed(42)
np.random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

PROPERTY_TYPES = ["1LDK", "2LDK", "3LDK", "一戸建て"]
STAFF_IDS = ["STAFF-01", "STAFF-02", "STAFF-03", "STAFF-04", "STAFF-05", "STAFF-06"]
AREAS = ["渋谷", "新宿", "品川", "池袋"]

dates = pd.date_range("2024-01-01", "2024-01-20", freq="D")

TOTAL = 480
PER_STYLE = 160


def gen_rows(start_idx, count):
    rows = []
    for i in range(count):
        visit_num = start_idx + i + 1
        visit_id = f"VIS-{visit_num:04d}"
        visit_date = dates[random.randint(0, len(dates) - 1)]
        property_type = random.choice(PROPERTY_TYPES)
        area = random.choice(AREAS)
        staff_id = random.choice(STAFF_IDS)
        asking_price = random.randint(2000, 8000)
        visit_count_cumulative = random.randint(1, 10)
        is_contracted = 1 if random.random() < 0.30 else 0
        if is_contracted == 1:
            days_to_contract = random.randint(5, 60)
        else:
            days_to_contract = None
        rows.append({
            "visit_date": visit_date,
            "visit_id": visit_id,
            "property_type": property_type,
            "area": area,
            "staff_id": staff_id,
            "asking_price": asking_price,
            "visit_count_cumulative": visit_count_cumulative,
            "days_to_contract": days_to_contract,
            "is_contracted": is_contracted,
        })
    return rows


rows_a = gen_rows(0, PER_STYLE)
rows_b = gen_rows(PER_STYLE, PER_STYLE)
rows_c = gen_rows(PER_STYLE * 2, PER_STYLE)

# StyleA: Japanese columns, date YYYY/MM/DD
df_a = pd.DataFrame(rows_a)
df_a_out = pd.DataFrame()
df_a_out["内見日"] = df_a["visit_date"].dt.strftime("%Y/%m/%d")
df_a_out["内見ID"] = df_a["visit_id"]
df_a_out["物件タイプ"] = df_a["property_type"]
df_a_out["エリア"] = df_a["area"]
df_a_out["担当者ID"] = df_a["staff_id"]
df_a_out["物件価格(万円)"] = df_a["asking_price"]
df_a_out["累計内見数"] = df_a["visit_count_cumulative"]
df_a_out["成約日数"] = df_a["days_to_contract"]
df_a_out["成約フラグ"] = df_a["is_contracted"]
df_a_out.to_csv(os.path.join(DATA_DIR, "visits_styleA.csv"), index=False, encoding="utf-8-sig")
print("[OK] StyleA saved: visits_styleA.csv ({} rows)".format(len(df_a_out)))

# StyleB: English columns, date YYYY-MM-DD
df_b = pd.DataFrame(rows_b)
df_b_out = pd.DataFrame()
df_b_out["VisitDate"] = df_b["visit_date"].dt.strftime("%Y-%m-%d")
df_b_out["VisitID"] = df_b["visit_id"]
df_b_out["PropertyType"] = df_b["property_type"]
df_b_out["Area"] = df_b["area"]
df_b_out["StaffID"] = df_b["staff_id"]
df_b_out["AskingPrice"] = df_b["asking_price"]
df_b_out["VisitCountCumulative"] = df_b["visit_count_cumulative"]
df_b_out["DaysToContract"] = df_b["days_to_contract"]
df_b_out["IsContracted"] = df_b["is_contracted"]
df_b_out.to_csv(os.path.join(DATA_DIR, "visits_styleB.csv"), index=False, encoding="utf-8-sig")
print("[OK] StyleB saved: visits_styleB.csv ({} rows)".format(len(df_b_out)))

# StyleC: Variant Japanese, date YYYY/MM/DD
df_c = pd.DataFrame(rows_c)
df_c_out = pd.DataFrame()
df_c_out["見学日"] = df_c["visit_date"].dt.strftime("%Y/%m/%d")
df_c_out["見学番号"] = df_c["visit_id"]
df_c_out["部屋タイプ"] = df_c["property_type"]
df_c_out["地域"] = df_c["area"]
df_c_out["担当ID"] = df_c["staff_id"]
df_c_out["価格"] = df_c["asking_price"]
df_c_out["見学累計回数"] = df_c["visit_count_cumulative"]
df_c_out["成約所要日"] = df_c["days_to_contract"]
df_c_out["成約"] = df_c["is_contracted"]
df_c_out.to_csv(os.path.join(DATA_DIR, "visits_styleC.csv"), index=False, encoding="utf-8-sig")
print("[OK] StyleC saved: visits_styleC.csv ({} rows)".format(len(df_c_out)))

print("[OK] All sample data generated. Total: {} rows".format(TOTAL))

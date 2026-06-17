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

SHOPS = ["東店", "西店", "北店"]
WORK_TYPES = ["オイル交換", "タイヤ交換", "車検", "一般修理"]
TECHS = [f"TECH-{i:02d}" for i in range(1, 11)]
STATUSES = ["完了", "作業中", "再入庫"]
STATUS_WEIGHTS = [0.80, 0.15, 0.05]

N_TOTAL = 480
N_EACH = 160  # 480 / 3

def make_base_records(start_id, n):
    records = []
    dates = pd.date_range("2024-01-01", "2024-01-20", periods=n)
    for i in range(n):
        oid = f"ORD-{start_id + i:04d}"
        order_date = dates[i].strftime("%Y-%m-%d")
        shop = random.choice(SHOPS)
        wtype = random.choice(WORK_TYPES)
        tech = random.choice(TECHS)
        est = random.randint(1, 5)
        act = random.randint(1, 8)
        labor = random.randint(5000, 80000)
        parts = random.randint(0, 50000)
        status = random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
        records.append({
            "order_date": order_date,
            "order_id": oid,
            "shop_name": shop,
            "work_type": wtype,
            "tech_id": tech,
            "estimated_days": est,
            "actual_days": act,
            "labor_cost": labor,
            "parts_cost": parts,
            "status": status,
        })
    return records

# --- Style A (Japanese columns, date YYYY/MM/DD) ---
records_a = make_base_records(1, N_EACH)
df_a = pd.DataFrame(records_a)
df_a["order_date"] = df_a["order_date"].str.replace("-", "/")
df_a = df_a.rename(columns={
    "order_date": "受付日",
    "order_id": "依頼番号",
    "shop_name": "店舗名",
    "work_type": "作業区分",
    "tech_id": "担当技術者",
    "estimated_days": "予定日数",
    "actual_days": "実績日数",
    "labor_cost": "工賃",
    "parts_cost": "部品代",
    "status": "ステータス",
})
df_a.to_csv(os.path.join(DATA_DIR, "orders_styleA.csv"), index=False, encoding="utf-8-sig")
print(f"[OK] StyleA: {len(df_a)} rows -> data/orders_styleA.csv")

# --- Style B (English columns, date YYYY-MM-DD) ---
records_b = make_base_records(N_EACH + 1, N_EACH)
df_b = pd.DataFrame(records_b)
STATUS_EN = {"完了": "Completed", "作業中": "InProgress", "再入庫": "Returned"}
df_b["status"] = df_b["status"].map(STATUS_EN)
df_b = df_b.rename(columns={
    "order_date": "OrderDate",
    "order_id": "OrderID",
    "shop_name": "ShopName",
    "work_type": "WorkType",
    "tech_id": "TechID",
    "estimated_days": "EstimatedDays",
    "actual_days": "ActualDays",
    "labor_cost": "LaborCost",
    "parts_cost": "PartsCost",
    "status": "Status",
})
df_b.to_csv(os.path.join(DATA_DIR, "orders_styleB.csv"), index=False, encoding="utf-8-sig")
print(f"[OK] StyleB: {len(df_b)} rows -> data/orders_styleB.csv")

# --- Style C (variant Japanese, date YYYY/MM/DD) ---
records_c = make_base_records(N_EACH * 2 + 1, N_EACH)
df_c = pd.DataFrame(records_c)
df_c["order_date"] = df_c["order_date"].str.replace("-", "/")
df_c = df_c.rename(columns={
    "order_date": "入庫日",
    "order_id": "作業番号",
    "shop_name": "工場名",
    "work_type": "整備種別",
    "tech_id": "技術者ID",
    "estimated_days": "見込み日数",
    "actual_days": "完了日数",
    "labor_cost": "技術料",
    "parts_cost": "部品費",
    "status": "進捗",
})
df_c.to_csv(os.path.join(DATA_DIR, "orders_styleC.csv"), index=False, encoding="utf-8-sig")
print(f"[OK] StyleC: {len(df_c)} rows -> data/orders_styleC.csv")

print(f"[OK] Total: {N_EACH * 3} rows generated (3 styles x {N_EACH} rows each)")

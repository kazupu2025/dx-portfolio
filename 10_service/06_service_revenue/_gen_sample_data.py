# -*- coding: utf-8 -*-
"""
C-45: サービス別売上・原価レポート
サンプルデータ生成スクリプト (3スタイル)
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import date, timedelta

random.seed(42)
np.random.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

SERVICES = [
    ("SVC-001", "清掃"),
    ("SVC-002", "警備"),
    ("SVC-003", "設備管理"),
    ("SVC-004", "受付代行"),
    ("SVC-005", "IT保守"),
    ("SVC-006", "コールセンター"),
    ("SVC-007", "警備巡回"),
    ("SVC-008", "施設管理"),
]

CATEGORIES = ["定期契約", "スポット", "複合"]
CLIENTS = ["CLI-001", "CLI-002", "CLI-003", "CLI-004", "CLI-005"]

START_DATE = date(2024, 1, 1)
END_DATE = date(2024, 1, 12)

# 赤字が必ず発生する組み合わせ
DEFICIT_COMBOS = {
    ("SVC-003", "CLI-002"),
    ("SVC-006", "CLI-004"),
    ("SVC-008", "CLI-001"),
}


def gen_dates():
    dates = []
    d = START_DATE
    while d <= END_DATE:
        dates.append(d)
        d += timedelta(days=1)
    return dates


def gen_rows():
    rows = []
    dates = gen_dates()
    cat_cycle = 0
    for d in dates:
        for svc_id, svc_name in SERVICES:
            for cli in CLIENTS:
                revenue = random.randint(50000, 500000)
                if (svc_id, cli) in DEFICIT_COMBOS:
                    cost = int(revenue * random.uniform(1.05, 1.30))
                else:
                    cost = random.randint(20000, min(int(revenue * 0.85), 350000))
                category = CATEGORIES[cat_cycle % 3]
                cat_cycle += 1
                rows.append({
                    "sale_date": d,
                    "service_id": svc_id,
                    "service_name": svc_name,
                    "category": category,
                    "client_id": cli,
                    "revenue": revenue,
                    "cost": cost,
                })
    return rows


def main():
    rows = gen_rows()
    df_base = pd.DataFrame(rows)

    # --- Style A (標準日本語、日付 YYYY/MM/DD) ---
    df_a = df_base.copy()
    df_a["sale_date"] = df_a["sale_date"].apply(lambda d: d.strftime("%Y/%m/%d"))
    df_a = df_a.rename(columns={
        "sale_date": "売上日",
        "service_id": "サービスID",
        "service_name": "サービス名",
        "category": "カテゴリ",
        "client_id": "クライアントID",
        "revenue": "売上金額",
        "cost": "原価",
    })
    path_a = os.path.join(OUTPUT_DIR, "service_revenue_styleA.csv")
    df_a.to_csv(path_a, index=False, encoding="utf-8-sig")
    print(f"[OK] StyleA: {len(df_a)} rows -> {path_a}")

    # --- Style B (English、日付 YYYY-MM-DD) ---
    df_b = df_base.copy()
    df_b["sale_date"] = df_b["sale_date"].apply(lambda d: d.strftime("%Y-%m-%d"))
    df_b = df_b.rename(columns={
        "sale_date": "SaleDate",
        "service_id": "ServiceID",
        "service_name": "ServiceName",
        "category": "Category",
        "client_id": "ClientID",
        "revenue": "Revenue",
        "cost": "Cost",
    })
    path_b = os.path.join(OUTPUT_DIR, "service_revenue_styleB.csv")
    df_b.to_csv(path_b, index=False, encoding="utf-8-sig")
    print(f"[OK] StyleB: {len(df_b)} rows -> {path_b}")

    # --- Style C (バリアント日本語、日付 YYYY/MM/DD) ---
    df_c = df_base.copy()
    df_c["sale_date"] = df_c["sale_date"].apply(lambda d: d.strftime("%Y/%m/%d"))
    df_c = df_c.rename(columns={
        "sale_date": "計上日",
        "service_id": "サービスコード",
        "service_name": "サービス区分",
        "category": "契約種別",
        "client_id": "顧客ID",
        "revenue": "売上高",
        "cost": "費用",
    })
    path_c = os.path.join(OUTPUT_DIR, "service_revenue_styleC.csv")
    df_c.to_csv(path_c, index=False, encoding="utf-8-sig")
    print(f"[OK] StyleC: {len(df_c)} rows -> {path_c}")

    print(f"\n[OK] Total rows per style: {len(df_base)}")
    print(f"[OK] Data generation complete.")


if __name__ == "__main__":
    main()

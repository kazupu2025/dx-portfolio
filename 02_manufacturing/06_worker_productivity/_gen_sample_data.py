"""サンプルデータ生成スクリプト - 3スタイルのCSVを data/ に生成"""
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

WORKERS = [f"WRK-{i:03d}" for i in range(1, 31)]   # WRK-001 ~ WRK-030
LINES = ["LINE-A", "LINE-B", "LINE-C", "LINE-D"]
PROCESSES = ["組立", "溶接", "検査", "梱包"]
DATES_AC = pd.date_range("2024-01-01", "2024-01-15")


def gen_base_rows():
    rows = []
    for date in DATES_AC:
        for worker in WORKERS:
            line = random.choice(LINES)
            process = random.choice(PROCESSES)
            production_qty = random.randint(40, 200)
            defect_qty = random.randint(0, max(1, int(production_qty * 0.10)))
            work_hours = round(random.uniform(6.0, 10.0), 1)
            overtime_hours = round(random.uniform(0.0, 3.0), 1)
            rows.append({
                "date": date,
                "worker_id": worker,
                "line": line,
                "process": process,
                "production_qty": production_qty,
                "defect_qty": defect_qty,
                "work_hours": work_hours,
                "overtime_hours": overtime_hours,
            })
    return rows


rows = gen_base_rows()
n = len(rows)
split1 = n // 3
split2 = 2 * n // 3

# Style A (standard Japanese, date=YYYY/MM/DD)
df_a = pd.DataFrame([{
    "作業日": r["date"].strftime("%Y/%m/%d"),
    "作業員ID": r["worker_id"],
    "ライン": r["line"],
    "工程": r["process"],
    "生産数量": r["production_qty"],
    "不良数": r["defect_qty"],
    "作業時間": r["work_hours"],
    "残業時間": r["overtime_hours"],
} for r in rows[:split1]])

# Style B (English, date=YYYY-MM-DD)
df_b = pd.DataFrame([{
    "WorkDate": r["date"].strftime("%Y-%m-%d"),
    "WorkerID": r["worker_id"],
    "Line": r["line"],
    "Process": r["process"],
    "ProductionQty": r["production_qty"],
    "DefectQty": r["defect_qty"],
    "WorkHours": r["work_hours"],
    "OvertimeHours": r["overtime_hours"],
} for r in rows[split1:split2]])

# Style C (variant Japanese, date=YYYY/MM/DD)
df_c = pd.DataFrame([{
    "日付": r["date"].strftime("%Y/%m/%d"),
    "従業員番号": r["worker_id"],
    "製造ライン": r["line"],
    "作業区分": r["process"],
    "生産実績": r["production_qty"],
    "不良品数": r["defect_qty"],
    "稼働時間": r["work_hours"],
    "残業": r["overtime_hours"],
} for r in rows[split2:]])

df_a.to_csv(DATA_DIR / "worker_prod_styleA_202401.csv", index=False, encoding="utf-8-sig")
df_b.to_csv(DATA_DIR / "worker_prod_styleB_202401.csv", index=False, encoding="utf-8-sig")
df_c.to_csv(DATA_DIR / "worker_prod_styleC_202401.csv", index=False, encoding="utf-8-sig")

print(f"生成完了: A={len(df_a)}行, B={len(df_b)}行, C={len(df_c)}行, 合計={len(df_a)+len(df_b)+len(df_c)}行")

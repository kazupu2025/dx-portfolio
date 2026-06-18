# -*- coding: utf-8 -*-
"""
C-58: 建設 x 経理・財務 -- 工事原価・予算実績管理パイプライン
サンプルデータ生成スクリプト

480件を3スタイルに分割（各160件）
StyleA: 標準日本語列名（日付 YYYY/MM/DD）
StyleB: 英語列名（日付 YYYY-MM-DD）
StyleC: バリアント日本語列名（日付 YYYY/MM/DD）
"""

import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

PROJECTS = [f"PROJ-{i:02d}" for i in range(1, 9)]  # PROJ-01 ~ PROJ-08
WORK_TYPES = ["土工", "コンクリート工", "鉄筋工", "仮設工"]
COST_CATEGORIES = ["材料費", "労務費", "外注費"]

START_DATE = date(2024, 1, 1)
END_DATE = date(2024, 1, 20)

TOTAL_RECORDS = 480
PER_STYLE = 160  # 各スタイル160件


def get_dates() -> list[date]:
    """2024-01-01 ~ 2024-01-20 の日付リスト"""
    dates = []
    d = START_DATE
    while d <= END_DATE:
        dates.append(d)
        d += timedelta(days=1)
    return dates


def generate_records(start_id: int, count: int) -> list[dict]:
    """内部レコードを生成"""
    dates = get_dates()
    records = []
    for i in range(count):
        rec_id = start_id + i
        budget = random.randint(100000, 2000000)
        # actual = budget * (0.7 ~ 1.3)
        ratio = 0.7 + random.random() * 0.6  # 0.7 ~ 1.3
        actual = int(budget * ratio)
        is_over = 1 if actual > budget else 0

        records.append({
            "record_date": random.choice(dates),
            "record_id": f"CST-{rec_id:04d}",
            "project_no": random.choice(PROJECTS),
            "work_type": random.choice(WORK_TYPES),
            "cost_category": random.choice(COST_CATEGORIES),
            "budget_amount": budget,
            "actual_amount": actual,
            "is_over_budget": is_over,
        })
    return records


def to_style_a(rec: dict) -> dict:
    """StyleA: 標準日本語列名（日付 YYYY/MM/DD）"""
    return {
        "計上日": rec["record_date"].strftime("%Y/%m/%d"),
        "記録ID": rec["record_id"],
        "工事番号": rec["project_no"],
        "工種": rec["work_type"],
        "費目": rec["cost_category"],
        "予算額": rec["budget_amount"],
        "実績額": rec["actual_amount"],
        "予算超過": rec["is_over_budget"],
    }


def to_style_b(rec: dict) -> dict:
    """StyleB: 英語列名（日付 YYYY-MM-DD）"""
    return {
        "RecordDate": rec["record_date"].strftime("%Y-%m-%d"),
        "RecordID": rec["record_id"],
        "ProjectNo": rec["project_no"],
        "WorkType": rec["work_type"],
        "CostCategory": rec["cost_category"],
        "BudgetAmount": rec["budget_amount"],
        "ActualAmount": rec["actual_amount"],
        "IsOverBudget": rec["is_over_budget"],
    }


def to_style_c(rec: dict) -> dict:
    """StyleC: バリアント日本語列名（日付 YYYY/MM/DD）"""
    return {
        "日付": rec["record_date"].strftime("%Y/%m/%d"),
        "管理番号": rec["record_id"],
        "案件番号": rec["project_no"],
        "作業区分": rec["work_type"],
        "原価区分": rec["cost_category"],
        "予定金額": rec["budget_amount"],
        "実際金額": rec["actual_amount"],
        "オーバー": rec["is_over_budget"],
    }


def main():
    # StyleA: CST-0001 ~ CST-0160
    recs_a = generate_records(start_id=1, count=PER_STYLE)
    df_a = pd.DataFrame([to_style_a(r) for r in recs_a])
    path_a = DATA_DIR / "costs_styleA_202401.csv"
    df_a.to_csv(path_a, index=False, encoding="utf-8-sig")
    print(f"Created {path_a.name}: {len(df_a)} rows (StyleA)")

    # StyleB: CST-0161 ~ CST-0320
    recs_b = generate_records(start_id=161, count=PER_STYLE)
    df_b = pd.DataFrame([to_style_b(r) for r in recs_b])
    path_b = DATA_DIR / "costs_styleB_202401.csv"
    df_b.to_csv(path_b, index=False, encoding="utf-8-sig")
    print(f"Created {path_b.name}: {len(df_b)} rows (StyleB)")

    # StyleC: CST-0321 ~ CST-0480
    recs_c = generate_records(start_id=321, count=PER_STYLE)
    df_c = pd.DataFrame([to_style_c(r) for r in recs_c])
    path_c = DATA_DIR / "costs_styleC_202401.csv"
    df_c.to_csv(path_c, index=False, encoding="utf-8-sig")
    print(f"Created {path_c.name}: {len(df_c)} rows (StyleC)")

    total = len(df_a) + len(df_b) + len(df_c)
    print(f"\n合計: {total} 行 (StyleA={len(df_a)}, StyleB={len(df_b)}, StyleC={len(df_c)})")


if __name__ == "__main__":
    main()

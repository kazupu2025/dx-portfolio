# -*- coding: utf-8 -*-
"""
C-25: 生産計画 vs 実績 差異分析パイプライン
サンプルデータ生成スクリプト
"""
import random
import csv
import os
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

LINES = ["LINE-A", "LINE-B", "LINE-C", "LINE-D", "LINE-E"]
CATEGORIES = ["電子部品", "機械部品", "樹脂成型", "金属加工"]

START_DATE = date(2024, 1, 1)
END_DATE = date(2024, 1, 31)


def date_range(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def gen_row_base():
    """共通の数値データを生成"""
    planned = random.randint(200, 800)
    # 10%の確率で低達成率（<0.8）
    if random.random() < 0.10:
        rate = random.uniform(0.60, 0.79)
    else:
        rate = random.uniform(0.80, 1.10)
    actual = max(0, int(planned * rate))
    defect = int(actual * random.uniform(0.00, 0.05))
    work_hours = round(random.uniform(6.0, 12.0), 1)
    return planned, actual, defect, work_hours


def gen_style_a(num_rows_target: int) -> None:
    """スタイルA: 標準日本語列名 / YYYY/MM/DD"""
    rows = []
    dates = list(date_range(START_DATE, END_DATE))
    while len(rows) < num_rows_target:
        for d in dates:
            for line in LINES:
                for cat in CATEGORIES:
                    if len(rows) >= num_rows_target:
                        break
                    planned, actual, defect, work_hours = gen_row_base()
                    rows.append({
                        "日付": d.strftime("%Y/%m/%d"),
                        "ライン名": line,
                        "製品カテゴリ": cat,
                        "計画数量": planned,
                        "実績数量": actual,
                        "不良数": defect,
                        "作業時間": work_hours,
                    })

    out_path = DATA_DIR / "production_styleA_202401.csv"
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] StyleA generated: {len(rows)} rows -> {out_path}")


def gen_style_b(num_rows_target: int) -> None:
    """スタイルB: 英語列名 / YYYY-MM-DD"""
    rows = []
    dates = list(date_range(START_DATE, END_DATE))
    while len(rows) < num_rows_target:
        for d in dates:
            for line in LINES:
                for cat in CATEGORIES:
                    if len(rows) >= num_rows_target:
                        break
                    planned, actual, defect, work_hours = gen_row_base()
                    rows.append({
                        "Date": d.strftime("%Y-%m-%d"),
                        "LineName": line,
                        "Category": cat,
                        "PlannedQty": planned,
                        "ActualQty": actual,
                        "DefectQty": defect,
                        "WorkHours": work_hours,
                    })

    out_path = DATA_DIR / "production_styleB_202401.csv"
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] StyleB generated: {len(rows)} rows -> {out_path}")


def gen_style_c(num_rows_target: int) -> None:
    """スタイルC: バリアント日本語列名 / YYYY/MM/DD"""
    rows = []
    dates = list(date_range(START_DATE, END_DATE))
    while len(rows) < num_rows_target:
        for d in dates:
            for line in LINES:
                for cat in CATEGORIES:
                    if len(rows) >= num_rows_target:
                        break
                    planned, actual, defect, work_hours = gen_row_base()
                    rows.append({
                        "集計日": d.strftime("%Y/%m/%d"),
                        "製造ライン": line,
                        "品種": cat,
                        "目標生産数": planned,
                        "生産実績数": actual,
                        "不良品数": defect,
                        "稼働時間": work_hours,
                    })

    out_path = DATA_DIR / "production_styleC_202401.csv"
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] StyleC generated: {len(rows)} rows -> {out_path}")


if __name__ == "__main__":
    # 各スタイル 140行以上で合計 420行以上
    gen_style_a(140)
    gen_style_b(140)
    gen_style_c(140)
    print("[OK] Sample data generation complete.")

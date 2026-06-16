"""
C-23: 不動産 x 経理・財務 -- 管理費・修繕費コスト分析パイプライン
サンプルデータ生成スクリプト

3スタイル x CSV、合計500行以上
物件50棟 x 費用区分5種 x 2024年1月
スタイルA: 標準日本語列名
スタイルB: 英語列名
スタイルC: 別表記列名
"""

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

random.seed(42)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

AREAS = ["渋谷区", "新宿区", "港区", "品川区", "目黒区"]
PROPERTY_TYPES = ["マンション", "アパート", "テナントビル", "戸建て"]
COST_CATEGORIES = ["管理費", "定期修繕", "緊急修繕", "清掃費", "設備点検"]

# 費用区分別の金額レンジ (円)
COST_RANGE = {
    "管理費": (50000, 200000),
    "定期修繕": (100000, 800000),
    "緊急修繕": (80000, 1200000),
    "清掃費": (30000, 100000),
    "設備点検": (40000, 150000),
}

# 業者名リスト
VENDORS = [
    "山田建設", "鈴木メンテナンス", "東京管理サービス", "ABC修繕", "グリーン清掃",
    "田中設備", "ミドリ建築", "サンライズ不動産管理", "関東メンテ", "スターハウス",
    "フジ設備管理", "東和修繕", "クリーンプロ", "ニッケン建設", "ハウスケア",
]


def generate_properties(n: int = 50) -> list[dict]:
    """物件マスタを生成"""
    properties = []
    for i in range(1, n + 1):
        area = AREAS[i % len(AREAS)]
        prop_type = PROPERTY_TYPES[i % len(PROPERTY_TYPES)]
        properties.append({
            "property_id": f"P{i:03d}",
            "property_name": f"{area}{prop_type}{i:03d}号",
            "area": area,
            "property_type": prop_type,
        })
    return properties


def get_occurrence_dates(year: int = 2024, month: int = 1) -> list[date]:
    """対象月の全日付を返す"""
    days = []
    d = date(year, month, 1)
    while d.month == month:
        days.append(d)
        d += timedelta(days=1)
    return days


def generate_cost_record(prop: dict, d: date, style_idx: int) -> dict:
    """1物件1日の費用レコードを生成"""
    cat = random.choice(COST_CATEGORIES)
    lo, hi = COST_RANGE[cat]
    amount = random.randint(lo, hi)

    # 緊急区分: 緊急修繕の20%が緊急
    is_urgent = (cat == "緊急修繕") and (random.random() < 0.20)

    vendor = random.choice(VENDORS)

    return {
        "property_id": prop["property_id"],
        "property_name": prop["property_name"],
        "area": prop["area"],
        "property_type": prop["property_type"],
        "cost_category": cat,
        "occurrence_date": d,
        "cost_amount": amount,
        "vendor_name": vendor,
        "is_urgent": is_urgent,
    }


def to_style_a(rec: dict) -> dict:
    """スタイルA: 標準日本語列名"""
    return {
        "物件ID": rec["property_id"],
        "物件名": rec["property_name"],
        "エリア": rec["area"],
        "物件種別": rec["property_type"],
        "費用区分": rec["cost_category"],
        "発生日": rec["occurrence_date"].strftime("%Y/%m/%d"),
        "費用金額": rec["cost_amount"],
        "業者名": rec["vendor_name"],
        "緊急区分": rec["is_urgent"],
    }


def to_style_b(rec: dict) -> dict:
    """スタイルB: 英語列名"""
    return {
        "property_id": rec["property_id"],
        "property_name": rec["property_name"],
        "area": rec["area"],
        "property_type": rec["property_type"],
        "cost_category": rec["cost_category"],
        "occurrence_date": rec["occurrence_date"].strftime("%Y-%m-%d"),
        "cost_amount": rec["cost_amount"],
        "vendor_name": rec["vendor_name"],
        "is_urgent": rec["is_urgent"],
    }


def to_style_c(rec: dict) -> dict:
    """スタイルC: 別表記列名"""
    return {
        "管理番号": rec["property_id"],
        "建物名": rec["property_name"],
        "地区": rec["area"],
        "種別": rec["property_type"],
        "費目": rec["cost_category"],
        "計上日": rec["occurrence_date"].strftime("%Y年%m月%d日"),
        "金額": rec["cost_amount"],
        "業者": rec["vendor_name"],
        "緊急対応": rec["is_urgent"],
    }


def main():
    properties = generate_properties(n=50)
    dates = get_occurrence_dates()

    configs = [
        ("A", to_style_a, "maintenance_A_202401.csv"),
        ("B", to_style_b, "maintenance_B_202401.csv"),
        ("C", to_style_c, "maintenance_C_202401.csv"),
    ]

    # 各スタイルで異なる物件グループを割り当て (スタイルA: P001-P020, B: P021-P035, C: P036-P050)
    style_props = {
        "A": properties[0:20],
        "B": properties[20:35],
        "C": properties[35:50],
    }

    # 各物件に対して費用レコードを複数生成（合計500行以上になるよう調整）
    for style, converter, filename in configs:
        rows = []
        props = style_props[style]
        # 各物件 x 月間複数の費用レコード（約10件/物件）
        for prop in props:
            # その月にランダムな日を選んで複数レコード生成
            n_records = random.randint(8, 12)
            chosen_dates = random.choices(dates, k=n_records)
            for d in chosen_dates:
                rec = generate_cost_record(prop, d, ord(style) - ord("A"))
                rows.append(converter(rec))

        df = pd.DataFrame(rows)
        out_path = DATA_DIR / filename
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"Created {filename}: {len(df)} rows (style {style})")

    total = sum(
        len(pd.read_csv(DATA_DIR / cfg[2], encoding="utf-8-sig"))
        for cfg in configs
    )
    print(f"\n合計: {total} 行 (3スタイル x 物件50棟)")


if __name__ == "__main__":
    main()

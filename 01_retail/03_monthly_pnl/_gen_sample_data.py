"""
C-19: 小売x経理・財務 月次収益・予実差異レポート
サンプルデータ生成スクリプト
3スタイル x 65行（週次13週x5店舗）= 195行以上を data/ に生成
"""
import random
import csv
import os

random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

STORES = [
    ("S001", "渋谷店"),
    ("S002", "新宿店"),
    ("S003", "池袋店"),
    ("S004", "横浜店"),
    ("S005", "大宮店"),
]

# 28週分（2024-W01 〜 2024-W28）: 28週 x 5店舗 = 140行/CSV x 3 = 420行以上
WEEKS = [f"2024-W{str(w).zfill(2)}" for w in range(1, 29)]

# 店舗ごとの基準値（週次）
BASE_REVENUE = {
    "S001": 3_500_000,
    "S002": 4_000_000,
    "S003": 3_000_000,
    "S004": 2_800_000,
    "S005": 2_200_000,
}

# 赤字を発生させる店舗・週の組み合わせ（意図的に設定）
DEFICIT_CASES = {
    ("S003", "2024-W05"),
    ("S005", "2024-W09"),
    ("S005", "2024-W10"),
    ("S003", "2024-W18"),
    ("S004", "2024-W22"),
    ("S001", "2024-W25"),
}


def gen_row(store_id, store_name, period):
    planned_revenue = BASE_REVENUE[store_id]
    # 実績は予算の±15%以内でランダム変動
    variance_factor = random.uniform(0.85, 1.15)
    actual_revenue = round(planned_revenue * variance_factor)

    planned_cogs = round(planned_revenue * random.uniform(0.45, 0.55))
    actual_cogs_factor = random.uniform(0.85, 1.15)
    actual_cogs = round(planned_cogs * actual_cogs_factor)

    planned_labor = round(planned_revenue * random.uniform(0.15, 0.22))
    actual_labor_factor = random.uniform(0.85, 1.15)
    actual_labor = round(planned_labor * actual_labor_factor)

    planned_other = round(planned_revenue * random.uniform(0.05, 0.10))
    actual_other_factor = random.uniform(0.85, 1.15)
    actual_other = round(planned_other * actual_other_factor)

    # 赤字ケース: コストを意図的に増加させる
    if (store_id, period) in DEFICIT_CASES:
        actual_cogs = round(actual_revenue * random.uniform(0.70, 0.80))
        actual_labor = round(actual_revenue * random.uniform(0.20, 0.28))
        actual_other = round(actual_revenue * random.uniform(0.08, 0.14))

    return {
        "store_id": store_id,
        "store_name": store_name,
        "period": period,
        "planned_revenue": planned_revenue,
        "actual_revenue": actual_revenue,
        "planned_cogs": planned_cogs,
        "actual_cogs": actual_cogs,
        "planned_labor": planned_labor,
        "actual_labor": actual_labor,
        "planned_other": planned_other,
        "actual_other": actual_other,
    }


def write_style_a(rows):
    """スタイルA: 標準日本語ヘッダ"""
    path = os.path.join(DATA_DIR, "pnl_style_a.csv")
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "店舗ID", "店舗名", "年月",
            "売上予算", "売上実績",
            "原価予算", "原価実績",
            "人件費予算", "人件費実績",
            "その他費用予算", "その他費用実績",
        ])
        for r in rows:
            writer.writerow([
                r["store_id"], r["store_name"], r["period"],
                r["planned_revenue"], r["actual_revenue"],
                r["planned_cogs"], r["actual_cogs"],
                r["planned_labor"], r["actual_labor"],
                r["planned_other"], r["actual_other"],
            ])
    print(f"[A] {path} ({len(rows)} rows)")


def write_style_b(rows):
    """スタイルB: 英語ヘッダ"""
    path = os.path.join(DATA_DIR, "pnl_style_b.csv")
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "store_id", "store_name", "year_month",
            "planned_revenue", "actual_revenue",
            "planned_cogs", "actual_cogs",
            "planned_labor", "actual_labor",
            "planned_other", "actual_other",
        ])
        for r in rows:
            writer.writerow([
                r["store_id"], r["store_name"], r["period"],
                r["planned_revenue"], r["actual_revenue"],
                r["planned_cogs"], r["actual_cogs"],
                r["planned_labor"], r["actual_labor"],
                r["planned_other"], r["actual_other"],
            ])
    print(f"[B] {path} ({len(rows)} rows)")


def write_style_c(rows):
    """スタイルC: 別表記ヘッダ"""
    path = os.path.join(DATA_DIR, "pnl_style_c.csv")
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "店番", "店舗", "期間",
            "売上計画", "売上実績",
            "売上原価計画", "売上原価実績",
            "人件費計画", "人件費実績",
            "諸経費計画", "諸経費実績",
        ])
        for r in rows:
            writer.writerow([
                r["store_id"], r["store_name"], r["period"],
                r["planned_revenue"], r["actual_revenue"],
                r["planned_cogs"], r["actual_cogs"],
                r["planned_labor"], r["actual_labor"],
                r["planned_other"], r["actual_other"],
            ])
    print(f"[C] {path} ({len(rows)} rows)")


def main():
    all_rows = []
    for week in WEEKS:
        for store_id, store_name in STORES:
            all_rows.append(gen_row(store_id, store_name, week))

    print(f"Total rows per style: {len(all_rows)}")
    print(f"Total rows across all styles: {len(all_rows) * 3}")

    write_style_a(all_rows)
    write_style_b(all_rows)
    write_style_c(all_rows)

    print("Sample data generation complete.")


if __name__ == "__main__":
    main()

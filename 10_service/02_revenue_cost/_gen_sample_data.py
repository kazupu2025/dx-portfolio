"""
C-21: サービス別売上・原価分析パイプライン
サンプルデータ生成スクリプト
3スタイルのCSV（合計500行以上）を data/ に出力する
"""
import random
import csv
import os
from pathlib import Path

random.seed(42)

BASE = Path(__file__).parent
DATA_DIR = BASE / "data"
DATA_DIR.mkdir(exist_ok=True)

SERVICE_TYPES = ["SaaS利用料", "受託開発", "保守サポート", "コンサルティング", "研修・教育"]
DEPARTMENTS = ["開発部", "営業部", "CS部", "コンサル部"]
MONTHS = ["2024-01", "2024-02", "2024-03"]

# 直接原価率（ベース）
BASE_DIRECT_COST_RATIO = {
    "SaaS利用料": 0.20,
    "受託開発": 0.55,
    "保守サポート": 0.35,
    "コンサルティング": 0.40,
    "研修・教育": 0.30,
}

# 間接原価配賦率（ベース）
BASE_OVERHEAD_RATIO = {
    "SaaS利用料": 0.05,
    "受託開発": 0.10,
    "保守サポート": 0.08,
    "コンサルティング": 0.12,
    "研修・教育": 0.07,
}

CLIENTS_A = [
    "株式会社山田商事", "田中製造", "鈴木物産", "伊藤通信", "渡辺フード",
    "中村サービス", "小林商会", "加藤工業", "吉田産業", "山本企業",
    "松本グループ", "佐々木HD", "井上コーポ", "木村システム", "林テクノ",
    "清水ソリューション", "池田ネットワーク", "橋本デジタル", "山口イノベ", "石川メディア",
]

CLIENTS_EN = [
    "Yamada Trading Co.", "Tanaka Manufacturing", "Suzuki General Trading",
    "Ito Communications", "Watanabe Foods", "Nakamura Services",
    "Kobayashi Commerce", "Kato Industries", "Yoshida Industries", "Yamamoto Corp",
    "Matsumoto Group", "Sasaki Holdings", "Inoue Corporation", "Kimura Systems",
    "Hayashi Technology", "Shimizu Solutions", "Ikeda Networks", "Hashimoto Digital",
    "Yamaguchi Innovation", "Ishikawa Media",
]

SERVICE_MAP_EN = {
    "SaaS利用料": "SaaS",
    "受託開発": "Custom Development",
    "保守サポート": "Maintenance Support",
    "コンサルティング": "Consulting",
    "研修・教育": "Training",
}

DEPT_MAP_EN = {
    "開発部": "Development",
    "営業部": "Sales",
    "CS部": "CS",
    "コンサル部": "Consulting",
}


def gen_row(proj_id, style="A"):
    """1案件分のデータを生成"""
    service = random.choice(SERVICE_TYPES)
    dept = random.choice(DEPARTMENTS)
    month = random.choice(MONTHS)
    client_a = random.choice(CLIENTS_A)
    client_en = random.choice(CLIENTS_EN)

    # 売上金額: サービスによって規模が異なる
    if service == "SaaS利用料":
        revenue = random.randint(50000, 500000)
    elif service == "受託開発":
        revenue = random.randint(500000, 5000000)
    elif service == "保守サポート":
        revenue = random.randint(100000, 800000)
    elif service == "コンサルティング":
        revenue = random.randint(200000, 2000000)
    else:  # 研修
        revenue = random.randint(80000, 600000)

    base_ratio = BASE_DIRECT_COST_RATIO[service]
    variation = random.uniform(-0.10, 0.10)
    direct_ratio = max(0.05, base_ratio + variation)
    direct_cost = int(revenue * direct_ratio)

    overhead_ratio = BASE_OVERHEAD_RATIO[service] + random.uniform(-0.02, 0.02)
    overhead = int(revenue * max(0.02, overhead_ratio))

    hours_spent = random.randint(10, 500)

    is_completed_val = random.choice([True, False])

    if style == "A":
        return {
            "案件ID": proj_id,
            "顧客名": client_a,
            "サービス区分": service,
            "担当部門": dept,
            "契約月": month,
            "売上金額": revenue,
            "直接原価": direct_cost,
            "間接原価配賦": overhead,
            "担当者工数h": hours_spent,
            "完了フラグ": "完了" if is_completed_val else "未完了",
        }
    elif style == "B":
        return {
            "project_id": proj_id,
            "client_name": client_en,
            "service_type": SERVICE_MAP_EN[service],
            "department": DEPT_MAP_EN[dept],
            "contract_month": month,
            "revenue": revenue,
            "direct_cost": direct_cost,
            "allocated_overhead": overhead,
            "hours_spent": hours_spent,
            "is_completed": is_completed_val,
        }
    else:  # C
        return {
            "プロジェクトID": proj_id,
            "クライアント": client_a,
            "種別": service,
            "部署": dept,
            "月度": month,
            "売上高": revenue,
            "直接費": direct_cost,
            "間接費": overhead,
            "工数": hours_spent,
            "完了": "完了" if is_completed_val else "未完了",
        }


def generate_csv(style, n_rows, filename, start_id=1):
    rows = []
    for i in range(n_rows):
        proj_id = f"{style}-{start_id + i:04d}"
        rows.append(gen_row(proj_id, style=style))
    filepath = DATA_DIR / filename
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] {filepath} ({n_rows}行)")


if __name__ == "__main__":
    generate_csv("A", 180, "revenue_cost_styleA_202401.csv", start_id=1)
    generate_csv("B", 180, "revenue_cost_styleB_202401.csv", start_id=1001)
    generate_csv("C", 170, "revenue_cost_styleC_202401.csv", start_id=2001)
    total = 180 + 180 + 170
    print(f"\n合計 {total} 行のサンプルデータを data/ に生成しました。")

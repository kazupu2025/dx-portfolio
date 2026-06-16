"""
C-31: 契約更新アラート・期限管理パイプライン サンプルデータ生成スクリプト
顧客150人 x 3スタイル（スタイルA/B/C）のCSVを生成する。
完全な架空データ。実在法人を連想させる情報は含まない。
"""
import pandas as pd
import random
from pathlib import Path

random.seed(42)

BASE = Path(__file__).parent
DATA_DIR = BASE / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 基準日: 2024-02-01
BASE_DATE = pd.Timestamp("2024-02-01")

# 顧客コード: CUST-001〜CUST-150
customers = [f"CUST-{i:03d}" for i in range(1, 151)]

# 保険種別
insurance_types_ja = ["生命保険", "損害保険", "医療保険", "年金保険"]
insurance_types_en = ["Life", "Property", "Medical", "Annuity"]
insurance_types_var = ["生命", "損害", "医療", "年金"]

# 担当者5人
agents = ["田中", "佐藤", "鈴木", "高橋", "伊藤"]

# 年間保険料レンジ（円）
PREMIUM_RANGE = (50_000, 2_000_000)


def make_contract_no(style: str, seq: int) -> str:
    if style == "A":
        return f"CN-{2024000000 + seq:010d}"
    elif style == "B":
        return f"CON{seq:06d}"
    else:  # C
        return f"POL-{2024000000 + seq:010d}"


def compute_end_date(base: pd.Timestamp) -> pd.Timestamp:
    """
    更新パターン分布:
      30%: 期限切れ (end < base)
      25%: 30日以内 (緊急)
      25%: 31〜90日 (警告)
      20%: 91日以上 (正常)
    """
    r = random.random()
    if r < 0.30:
        # 期限切れ: 1〜365日前
        days_ago = random.randint(1, 365)
        return base - pd.Timedelta(days=days_ago)
    elif r < 0.55:
        # 緊急: 0〜30日後
        days_ahead = random.randint(0, 30)
        return base + pd.Timedelta(days=days_ahead)
    elif r < 0.80:
        # 警告: 31〜90日後
        days_ahead = random.randint(31, 90)
        return base + pd.Timedelta(days=days_ahead)
    else:
        # 正常: 91〜730日後
        days_ahead = random.randint(91, 730)
        return base + pd.Timedelta(days=days_ahead)


def gen_start_date(end_date: pd.Timestamp) -> pd.Timestamp:
    """契約開始日: 終了日から1〜5年前"""
    years = random.randint(1, 5)
    return end_date - pd.Timedelta(days=365 * years)


def gen_rows_style_a(n: int, seq_start: int) -> list:
    """スタイルA: 標準日本語列名、日付YYYY/MM/DD"""
    rows = []
    for i in range(n):
        end_date = compute_end_date(BASE_DATE)
        start_date = gen_start_date(end_date)
        cust = random.choice(customers)
        ins_type = random.choice(insurance_types_ja)
        agent = random.choice(agents)
        premium = random.randint(*PREMIUM_RANGE)

        rows.append({
            "契約番号": make_contract_no("A", seq_start + i),
            "顧客コード": cust,
            "保険種別": ins_type,
            "契約開始日": start_date.strftime("%Y/%m/%d"),
            "契約終了日": end_date.strftime("%Y/%m/%d"),
            "年間保険料": premium,
            "担当者": agent,
        })
    return rows


def gen_rows_style_b(n: int, seq_start: int) -> list:
    """スタイルB: 英語列名、日付YYYY-MM-DD"""
    rows = []
    for i in range(n):
        end_date = compute_end_date(BASE_DATE)
        start_date = gen_start_date(end_date)
        cust = random.choice(customers)
        ins_idx = random.randint(0, 3)
        agent = random.choice(agents)
        premium = random.randint(*PREMIUM_RANGE)

        rows.append({
            "ContractNo": make_contract_no("B", seq_start + i),
            "CustomerCode": cust,
            "InsuranceType": insurance_types_en[ins_idx],
            "StartDate": start_date.strftime("%Y-%m-%d"),
            "EndDate": end_date.strftime("%Y-%m-%d"),
            "AnnualPremium": premium,
            "AgentName": agent,
        })
    return rows


def gen_rows_style_c(n: int, seq_start: int) -> list:
    """スタイルC: バリアント日本語列名、日付YYYY/MM/DD"""
    rows = []
    for i in range(n):
        end_date = compute_end_date(BASE_DATE)
        start_date = gen_start_date(end_date)
        cust = random.choice(customers)
        ins_idx = random.randint(0, 3)
        agent = random.choice(agents)
        premium = random.randint(*PREMIUM_RANGE)

        rows.append({
            "証券番号": make_contract_no("C", seq_start + i),
            "顧客ID": cust,
            "商品区分": insurance_types_var[ins_idx],
            "開始日": start_date.strftime("%Y/%m/%d"),
            "満期日": end_date.strftime("%Y/%m/%d"),
            "年払保険料": premium,
            "担当営業": agent,
        })
    return rows


# 各スタイルの行数（合計 >= 400）
N_A = 160
N_B = 140
N_C = 120

rows_a = gen_rows_style_a(N_A, 1)
rows_b = gen_rows_style_b(N_B, N_A + 1)
rows_c = gen_rows_style_c(N_C, N_A + N_B + 1)

files = [
    ("01_契約データ_A_202401.csv", rows_a),
    ("02_contract_data_B_202401.csv", rows_b),
    ("03_契約データ_C_202401.csv", rows_c),
]

for filename, rows in files:
    df = pd.DataFrame(rows)
    df.to_csv(DATA_DIR / filename, index=False, encoding="utf-8-sig")
    print(f"Created {filename}: {len(df)} rows")

total = N_A + N_B + N_C
print(f"\nサンプルデータ生成完了（合計 {total} 行, 3スタイル）")

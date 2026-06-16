"""
C-26: 請求書突合・差異検出パイプライン サンプルデータ生成スクリプト
得意先20社 × 3スタイル（スタイルA/B/C）のCSVを生成する。
完全な架空データ。実在法人を連想させる情報は含まない。
"""
import pandas as pd
import random
from pathlib import Path

random.seed(42)

BASE = Path("C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/04_finance/03_invoice_reconciliation")
DATA_DIR = BASE / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 得意先コード: CLI-001〜CLI-020
clients = [f"CLI-{i:03d}" for i in range(1, 21)]

# 支払区分3種
payment_types_ja = ["銀行振込", "口座振替", "手形"]
payment_types_en = ["BankTransfer", "DirectDebit", "Bill"]
payment_types_var = ["振込", "自動振替", "約束手形"]

# 請求金額レンジ（円）
AMOUNT_RANGE = (50_000, 5_000_000)

# 差異パターン比率: 一致80%, 過少10%, 過払5%, 未入金5%
PATTERNS = ["match", "short", "over", "unpaid"]
WEIGHTS   = [0.80,   0.10,    0.05,   0.05]


def make_invoice_no(style: str, seq: int) -> str:
    if style == "A":
        return f"INV-{2024010000 + seq:08d}"
    elif style == "B":
        return f"INV{seq:06d}"
    else:  # C
        return f"DEN-{2024010000 + seq:08d}"


def make_amounts(pattern: str) -> tuple:
    """invoice_amount, received_amount を返す"""
    inv = random.randint(*AMOUNT_RANGE)
    if pattern == "match":
        rec = inv
    elif pattern == "short":
        # 過少入金: 1〜30%少ない
        shortage = int(inv * random.uniform(0.01, 0.30))
        rec = inv - shortage
    elif pattern == "over":
        # 過払: 1〜10%多い
        excess = int(inv * random.uniform(0.01, 0.10))
        rec = inv + excess
    else:  # unpaid
        rec = 0
    return inv, rec


def gen_rows_style_a(n: int, seq_start: int) -> list:
    """スタイルA: 標準日本語列名、日付YYYY/MM/DD"""
    rows = []
    for i in range(n):
        day = random.randint(1, 28)
        inv_date = f"2024/01/{day:02d}"
        rec_day = min(28, day + random.randint(7, 30))
        rec_date = f"2024/01/{rec_day:02d}" if rec_day <= 28 else f"2024/02/{rec_day - 28:02d}"

        client = random.choice(clients)
        pattern = random.choices(PATTERNS, WEIGHTS)[0]
        inv_amt, rec_amt = make_amounts(pattern)

        rows.append({
            "請求書番号": make_invoice_no("A", seq_start + i),
            "請求日":     inv_date,
            "得意先コード": client,
            "請求金額":   inv_amt,
            "入金金額":   rec_amt,
            "入金日":     rec_date if rec_amt > 0 else "",
            "支払区分":   random.choice(payment_types_ja),
        })
    return rows


def gen_rows_style_b(n: int, seq_start: int) -> list:
    """スタイルB: 英語列名、日付YYYY-MM-DD"""
    rows = []
    for i in range(n):
        day = random.randint(1, 28)
        inv_date = f"2024-01-{day:02d}"
        rec_day = min(28, day + random.randint(7, 30))
        rec_date = f"2024-01-{rec_day:02d}" if rec_day <= 28 else f"2024-02-{rec_day - 28:02d}"

        client = random.choice(clients)
        pattern = random.choices(PATTERNS, WEIGHTS)[0]
        inv_amt, rec_amt = make_amounts(pattern)

        rows.append({
            "InvoiceNo":       make_invoice_no("B", seq_start + i),
            "InvoiceDate":     inv_date,
            "ClientCode":      client,
            "InvoiceAmount":   inv_amt,
            "ReceivedAmount":  rec_amt,
            "ReceivedDate":    rec_date if rec_amt > 0 else "",
            "PaymentType":     random.choice(payment_types_en),
        })
    return rows


def gen_rows_style_c(n: int, seq_start: int) -> list:
    """スタイルC: バリアント日本語列名、日付YYYY/MM/DD"""
    rows = []
    for i in range(n):
        day = random.randint(1, 28)
        inv_date = f"2024/01/{day:02d}"
        rec_day = min(28, day + random.randint(7, 30))
        rec_date = f"2024/01/{rec_day:02d}" if rec_day <= 28 else f"2024/02/{rec_day - 28:02d}"

        client = random.choice(clients)
        pattern = random.choices(PATTERNS, WEIGHTS)[0]
        inv_amt, rec_amt = make_amounts(pattern)

        rows.append({
            "伝票番号":   make_invoice_no("C", seq_start + i),
            "発行日":     inv_date,
            "取引先CD":  client,
            "請求額":    inv_amt,
            "受領額":    rec_amt,
            "受取日":    rec_date if rec_amt > 0 else "",
            "決済方法":  random.choice(payment_types_var),
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
    ("01_請求データ_A_202401.csv", rows_a),
    ("02_invoice_data_B_202401.csv", rows_b),
    ("03_請求データ_C_202401.csv", rows_c),
]

for filename, rows in files:
    df = pd.DataFrame(rows)
    df.to_csv(DATA_DIR / filename, index=False, encoding="utf-8-sig")
    print(f"Created {filename}: {len(df)} rows")

total = N_A + N_B + N_C
print(f"\nサンプルデータ生成完了（合計 {total} 行, 3スタイル）")

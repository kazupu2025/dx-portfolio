# -*- coding: utf-8 -*-
"""
C-52: 保険契約問い合わせ・対応履歴分析パイプライン サンプルデータ生成スクリプト
480件を3スタイルに分割（各160件）して data/ に保存する。
完全な架空データ。実在情報を含まない。
"""
import pandas as pd
import numpy as np
import random
from pathlib import Path

random.seed(42)
np.random.seed(42)

BASE = Path("C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/04_finance/04_inquiry_analysis")
DATA_DIR = BASE / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 問い合わせ区分 5種
INQUIRY_TYPES = ["契約内容確認", "保険金請求", "解約手続き", "新規加入", "変更手続き"]
INQUIRY_TYPES_EN = ["ContractConfirm", "ClaimRequest", "Cancellation", "NewEnrollment", "ChangeRequest"]
INQUIRY_TYPES_VAR = ["契約照会", "給付請求", "解約", "新規契約", "契約変更"]

# チャネル 3種
CHANNELS_JA = ["電話", "メール", "窓口"]
CHANNELS_EN = ["Phone", "Email", "Counter"]
CHANNELS_VAR = ["TEL", "Mail", "来店"]

# オペレーター 8名
OPERATORS = [f"OP-{i:02d}" for i in range(1, 9)]

# 日付範囲 2024-01-01〜2024-01-20
DATES_JA = [f"2024/01/{d:02d}" for d in range(1, 21)]
DATES_EN = [f"2024-01-{d:02d}" for d in range(1, 21)]


def gen_row_base(seq: int):
    """共通のランダム値を生成"""
    date_idx = random.randint(0, 19)
    inquiry_type_idx = random.randint(0, 4)
    channel_idx = random.randint(0, 2)
    operator_id = random.choice(OPERATORS)
    handling_minutes = random.randint(5, 120)
    # 解決率85%
    is_resolved = 1 if random.random() < 0.85 else 0
    # 再問い合わせ率15%
    recontact_flag = 1 if random.random() < 0.15 else 0
    satisfaction = random.randint(1, 5)
    return date_idx, inquiry_type_idx, channel_idx, operator_id, handling_minutes, is_resolved, recontact_flag, satisfaction


def gen_rows_style_a(n: int, seq_start: int) -> list:
    """StyleA: 標準日本語列名、日付YYYY/MM/DD"""
    rows = []
    for i in range(n):
        date_idx, type_idx, ch_idx, op, mins, resolved, recontact, sat = gen_row_base(seq_start + i)
        rows.append({
            "問い合わせ日":    DATES_JA[date_idx],
            "問い合わせID":   f"INQ-{seq_start + i:04d}",
            "問い合わせ区分": INQUIRY_TYPES[type_idx],
            "チャネル":       CHANNELS_JA[ch_idx],
            "担当者ID":       op,
            "対応時間(分)":   mins,
            "解決フラグ":     resolved,
            "再問い合わせフラグ": recontact,
            "満足度":         sat,
        })
    return rows


def gen_rows_style_b(n: int, seq_start: int) -> list:
    """StyleB: English列名、日付YYYY-MM-DD"""
    rows = []
    for i in range(n):
        date_idx, type_idx, ch_idx, op, mins, resolved, recontact, sat = gen_row_base(seq_start + i)
        rows.append({
            "InquiryDate":    DATES_EN[date_idx],
            "InquiryID":      f"INQ-{seq_start + i:04d}",
            "InquiryType":    INQUIRY_TYPES_EN[type_idx],
            "Channel":        CHANNELS_EN[ch_idx],
            "OperatorID":     op,
            "HandlingMinutes": mins,
            "IsResolved":     resolved,
            "RecontactFlag":  recontact,
            "Satisfaction":   sat,
        })
    return rows


def gen_rows_style_c(n: int, seq_start: int) -> list:
    """StyleC: バリアント日本語列名、日付YYYY/MM/DD"""
    rows = []
    for i in range(n):
        date_idx, type_idx, ch_idx, op, mins, resolved, recontact, sat = gen_row_base(seq_start + i)
        rows.append({
            "受付日":    DATES_JA[date_idx],
            "受付番号":  f"INQ-{seq_start + i:04d}",
            "区分":      INQUIRY_TYPES_VAR[type_idx],
            "受付チャネル": CHANNELS_VAR[ch_idx],
            "対応者":    op,
            "処理時間":  mins,
            "解決":      resolved,
            "再連絡":    recontact,
            "CS評価":    sat,
        })
    return rows


N_A = 160
N_B = 160
N_C = 160

rows_a = gen_rows_style_a(N_A, 1)
rows_b = gen_rows_style_b(N_B, N_A + 1)
rows_c = gen_rows_style_c(N_C, N_A + N_B + 1)

files = [
    ("01_問い合わせ_A_202401.csv", rows_a),
    ("02_inquiry_data_B_202401.csv", rows_b),
    ("03_問い合わせ_C_202401.csv", rows_c),
]

for filename, rows in files:
    df = pd.DataFrame(rows)
    df.to_csv(DATA_DIR / filename, index=False, encoding="utf-8-sig")
    print(f"Created {filename}: {len(df)} rows")

total = N_A + N_B + N_C
print(f"\nSample data generated: {total} rows, 3 styles")

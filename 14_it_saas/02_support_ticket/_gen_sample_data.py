# -*- coding: utf-8 -*-
"""
C-60 IT/SaaS - カスタマーサポートチケット分析
サンプルデータ生成スクリプト
480件を3スタイルに分割（各160件）
"""

import os
import random
import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- 共通パラメータ ---
TOTAL = 480
PER_STYLE = 160
START_DATE = "2024-01-01"
END_DATE = "2024-01-20"

CATEGORIES = ["ログイン障害", "機能不具合", "請求問い合わせ", "使い方質問", "データ移行"]
PRIORITIES = ["高", "中", "低"]
AGENT_IDS = [f"AGT-{i:02d}" for i in range(1, 9)]  # AGT-01 ~ AGT-08
ESCALATION_REASONS = ["技術的複雑性", "顧客クレーム", "権限不足"]

ESCALATION_RATE = 0.15
RESOLVE_RATE = 0.90


def generate_base_records(n, id_offset):
    """共通のレコードデータを生成する"""
    dates = pd.date_range(START_DATE, END_DATE, freq="D")
    records = []
    for i in range(n):
        ticket_num = id_offset + i + 1
        ticket_id = f"TKT-{ticket_num:04d}"
        received_date = random.choice(dates).strftime("%Y-%m-%d")
        category = random.choice(CATEGORIES)
        priority = random.choice(PRIORITIES)
        agent_id = random.choice(AGENT_IDS)
        resolution_hours = random.randint(1, 72)
        is_escalated = 1 if random.random() < ESCALATION_RATE else 0
        escalation_reason = random.choice(ESCALATION_REASONS) if is_escalated == 1 else None
        satisfaction = random.randint(1, 5)
        is_resolved = 1 if random.random() < RESOLVE_RATE else 0
        records.append({
            "received_date": received_date,
            "ticket_id": ticket_id,
            "category": category,
            "priority": priority,
            "agent_id": agent_id,
            "resolution_hours": resolution_hours,
            "is_escalated": is_escalated,
            "escalation_reason": escalation_reason,
            "satisfaction": satisfaction,
            "is_resolved": is_resolved,
        })
    return records


def make_style_a(records):
    """StyleA: 標準日本語、日付YYYY/MM/DD"""
    rows = []
    for r in records:
        date_slash = r["received_date"].replace("-", "/")
        rows.append({
            "受付日": date_slash,
            "チケットID": r["ticket_id"],
            "カテゴリ": r["category"],
            "優先度": r["priority"],
            "担当者ID": r["agent_id"],
            "解決時間(h)": r["resolution_hours"],
            "エスカレーション": r["is_escalated"],
            "エスカレーション理由": r["escalation_reason"] if r["escalation_reason"] is not None else "",
            "満足度": r["satisfaction"],
            "解決済み": r["is_resolved"],
        })
    return pd.DataFrame(rows)


def make_style_b(records):
    """StyleB: English、日付YYYY-MM-DD"""
    priority_map = {"高": "High", "中": "Medium", "低": "Low"}
    rows = []
    for r in records:
        rows.append({
            "ReceivedDate": r["received_date"],
            "TicketID": r["ticket_id"],
            "Category": r["category"],
            "Priority": priority_map[r["priority"]],
            "AgentID": r["agent_id"],
            "ResolutionHours": r["resolution_hours"],
            "IsEscalated": r["is_escalated"],
            "EscalationReason": r["escalation_reason"] if r["escalation_reason"] is not None else "",
            "Satisfaction": r["satisfaction"],
            "IsResolved": r["is_resolved"],
        })
    return pd.DataFrame(rows)


def make_style_c(records):
    """StyleC: バリアント日本語、日付YYYY/MM/DD"""
    rows = []
    for r in records:
        date_slash = r["received_date"].replace("-", "/")
        rows.append({
            "起票日": date_slash,
            "案件番号": r["ticket_id"],
            "問い合わせ分類": r["category"],
            "緊急度": r["priority"],
            "対応者ID": r["agent_id"],
            "対応時間": r["resolution_hours"],
            "上申": r["is_escalated"],
            "上申理由": r["escalation_reason"] if r["escalation_reason"] is not None else "",
            "CS満足度": r["satisfaction"],
            "完了": r["is_resolved"],
        })
    return pd.DataFrame(rows)


def main():
    all_records = generate_base_records(TOTAL, id_offset=0)

    records_a = all_records[0:PER_STYLE]
    records_b = all_records[PER_STYLE:PER_STYLE * 2]
    records_c = all_records[PER_STYLE * 2:PER_STYLE * 3]

    df_a = make_style_a(records_a)
    df_b = make_style_b(records_b)
    df_c = make_style_c(records_c)

    out_a = os.path.join(OUTPUT_DIR, "tickets_styleA_202401.csv")
    out_b = os.path.join(OUTPUT_DIR, "tickets_styleB_202401.csv")
    out_c = os.path.join(OUTPUT_DIR, "tickets_styleC_202401.csv")

    df_a.to_csv(out_a, index=False, encoding="utf-8-sig")
    df_b.to_csv(out_b, index=False, encoding="utf-8-sig")
    df_c.to_csv(out_c, index=False, encoding="utf-8-sig")

    print(f"[OK] StyleA: {len(df_a)} records -> {out_a}")
    print(f"[OK] StyleB: {len(df_b)} records -> {out_b}")
    print(f"[OK] StyleC: {len(df_c)} records -> {out_c}")
    print(f"[OK] Total: {len(df_a) + len(df_b) + len(df_c)} records")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
C-60 IT/SaaS - カスタマーサポートチケット分析
データクレンジングスクリプト
3スタイルCSVを統一フォーマットに変換する
"""

import os
import pandas as pd

random_seed = 42  # シード（本スクリプトはrandom使用なし）

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- カラムマッピング ---
COLUMN_MAP = {
    # StyleA（標準日本語）
    "受付日": "received_date",
    "チケットID": "ticket_id",
    "カテゴリ": "category",
    "優先度": "priority",
    "担当者ID": "agent_id",
    "解決時間(h)": "resolution_hours",
    "エスカレーション": "is_escalated",
    "エスカレーション理由": "escalation_reason",
    "満足度": "satisfaction",
    "解決済み": "is_resolved",
    # StyleB（English）
    "ReceivedDate": "received_date",
    "TicketID": "ticket_id",
    "Category": "category",
    "Priority": "priority",
    "AgentID": "agent_id",
    "ResolutionHours": "resolution_hours",
    "IsEscalated": "is_escalated",
    "EscalationReason": "escalation_reason",
    "Satisfaction": "satisfaction",
    "IsResolved": "is_resolved",
    # StyleC（バリアント日本語）
    "起票日": "received_date",
    "案件番号": "ticket_id",
    "問い合わせ分類": "category",
    "緊急度": "priority",
    "対応者ID": "agent_id",
    "対応時間": "resolution_hours",
    "上申": "is_escalated",
    "上申理由": "escalation_reason",
    "CS満足度": "satisfaction",
    "完了": "is_resolved",
}

# 優先度の英語→日本語マッピング（StyleB用）
PRIORITY_MAP_EN_TO_JA = {
    "High": "高",
    "Medium": "中",
    "Low": "低",
}

# 出力カラム（CANONICAL_COLS）
CANONICAL_COLS = [
    "received_date",
    "ticket_id",
    "category",
    "priority",
    "agent_id",
    "resolution_hours",
    "is_escalated",
    "escalation_reason",
    "satisfaction",
    "is_resolved",
    "speed_grade",
    "cs_level",
    "source_file",
]


def load_and_rename(filepath):
    """CSVを読み込み、カラムを統一名にリネームする"""
    df = pd.read_csv(filepath, encoding="utf-8-sig", dtype=str)
    df = df.rename(columns=COLUMN_MAP)
    df["source_file"] = os.path.basename(filepath)
    return df


def normalize_date(series):
    """YYYY/MM/DD および YYYY-MM-DD を YYYY-MM-DD に統一する"""
    return pd.to_datetime(
        series.str.replace("/", "-", regex=False),
        format="%Y-%m-%d",
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")


def normalize_priority(series):
    """優先度をStyleBの英語から日本語に変換（既に日本語ならそのまま）"""
    return series.replace(PRIORITY_MAP_EN_TO_JA)


def add_derived_columns(df):
    """派生列を追加する"""
    df["resolution_hours"] = pd.to_numeric(df["resolution_hours"], errors="coerce")

    def speed_grade(h):
        if pd.isna(h):
            return None
        if h <= 4:
            return "迅速"
        elif h <= 24:
            return "標準"
        else:
            return "長時間"

    df["speed_grade"] = df["resolution_hours"].apply(speed_grade)

    df["satisfaction"] = pd.to_numeric(df["satisfaction"], errors="coerce")

    def cs_level(s):
        if pd.isna(s):
            return None
        if s >= 4:
            return "高満足"
        elif s >= 3:
            return "普通"
        else:
            return "低満足"

    df["cs_level"] = df["satisfaction"].apply(cs_level)
    return df


def cleanse_df(df):
    """単一DataFrameのクレンジング処理"""
    # 日付正規化
    df["received_date"] = normalize_date(df["received_date"])

    # 優先度正規化
    df["priority"] = normalize_priority(df["priority"])

    # 数値変換
    df["resolution_hours"] = pd.to_numeric(df["resolution_hours"], errors="coerce")
    df["is_escalated"] = pd.to_numeric(df["is_escalated"], errors="coerce").astype("Int64")
    df["satisfaction"] = pd.to_numeric(df["satisfaction"], errors="coerce")
    df["is_resolved"] = pd.to_numeric(df["is_resolved"], errors="coerce").astype("Int64")

    # escalation_reason: 空文字をNaNに統一
    df["escalation_reason"] = df["escalation_reason"].replace("", None)

    # 派生列追加
    df = add_derived_columns(df)

    return df


def main():
    files = [
        os.path.join(DATA_DIR, "tickets_styleA_202401.csv"),
        os.path.join(DATA_DIR, "tickets_styleB_202401.csv"),
        os.path.join(DATA_DIR, "tickets_styleC_202401.csv"),
    ]

    dfs = []
    for f in files:
        if not os.path.exists(f):
            print(f"[FAIL] File not found: {f}")
            continue
        df = load_and_rename(f)
        df = cleanse_df(df)
        dfs.append(df)
        print(f"[OK] Loaded: {os.path.basename(f)} -> {len(df)} records")

    if not dfs:
        print("[FAIL] No data loaded. Exiting.")
        return

    combined = pd.concat(dfs, ignore_index=True)

    # CANONICAL_COLSのみを出力
    for col in CANONICAL_COLS:
        if col not in combined.columns:
            combined[col] = None
    combined = combined[CANONICAL_COLS]

    out_path = os.path.join(OUTPUT_DIR, "cleaned_tickets_202401.csv")
    combined.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"[OK] Output: {out_path} -> {len(combined)} records")
    print(f"[OK] Columns: {list(combined.columns)}")


if __name__ == "__main__":
    main()

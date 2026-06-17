# -*- coding: utf-8 -*-
"""
C-45: サービス別売上・原価レポート
クレンジングスクリプト
"""

import os
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

COLUMN_MAP = {
    # Style A
    "売上日": "sale_date",
    "サービスID": "service_id",
    "サービス名": "service_name",
    "カテゴリ": "category",
    "クライアントID": "client_id",
    "売上金額": "revenue",
    "原価": "cost",
    # Style B
    "SaleDate": "sale_date",
    "ServiceID": "service_id",
    "ServiceName": "service_name",
    "Category": "category",
    "ClientID": "client_id",
    "Revenue": "revenue",
    "Cost": "cost",
    # Style C
    "計上日": "sale_date",
    "サービスコード": "service_id",
    "サービス区分": "service_name",
    "契約種別": "category",
    "顧客ID": "client_id",
    "売上高": "revenue",
    "費用": "cost",
}

CANONICAL_COLS = [
    "sale_date",
    "service_id",
    "service_name",
    "category",
    "client_id",
    "revenue",
    "cost",
    "gross_profit",
    "gross_margin",
    "profit_flag",
    "margin_grade",
    "source_file",
]


def normalize_date(series: pd.Series) -> pd.Series:
    """日付正規化: YYYY/MM/DD -> YYYY-MM-DD"""
    normalized = series.astype(str).str.replace("/", "-", regex=False)
    return pd.to_datetime(normalized, format="%Y-%m-%d").dt.strftime("%Y-%m-%d")


def compute_derived(df: pd.DataFrame) -> pd.DataFrame:
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["cost"] = pd.to_numeric(df["cost"], errors="coerce")

    df["gross_profit"] = df["revenue"] - df["cost"]
    df["gross_margin"] = np.where(
        df["revenue"] > 0,
        df["gross_profit"] / df["revenue"],
        np.nan,
    )
    df["profit_flag"] = df["gross_profit"].apply(
        lambda x: "赤字" if x < 0 else "黒字"
    )
    df["margin_grade"] = df["gross_margin"].apply(
        lambda x: "高利益" if (not np.isnan(x) and x >= 0.4)
        else ("中利益" if (not np.isnan(x) and x >= 0.2) else "低利益")
    )
    return df


def load_file(path: str) -> pd.DataFrame:
    fname = os.path.basename(path)
    df = pd.read_csv(path, encoding="utf-8-sig")
    df = df.rename(columns=COLUMN_MAP)
    df["sale_date"] = normalize_date(df["sale_date"])
    df = compute_derived(df)
    df["source_file"] = fname
    return df[CANONICAL_COLS]


def main():
    files = [
        os.path.join(DATA_DIR, "service_revenue_styleA.csv"),
        os.path.join(DATA_DIR, "service_revenue_styleB.csv"),
        os.path.join(DATA_DIR, "service_revenue_styleC.csv"),
    ]

    dfs = []
    for f in files:
        if not os.path.exists(f):
            print(f"[FAIL] File not found: {f}")
            continue
        df = load_file(f)
        print(f"[OK] Loaded {len(df)} rows from {os.path.basename(f)}")
        dfs.append(df)

    if not dfs:
        print("[FAIL] No data loaded. Exiting.")
        return

    combined = pd.concat(dfs, ignore_index=True)
    out_path = os.path.join(OUTPUT_DIR, "cleaned_revenue_202401.csv")
    combined.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n[OK] Combined: {len(combined)} rows -> {out_path}")
    print("[OK] Cleansing complete.")


if __name__ == "__main__":
    main()

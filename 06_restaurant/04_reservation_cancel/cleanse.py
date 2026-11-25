# -*- coding: utf-8 -*-
"""
C-38: 予約キャンセル集計・傾向分析パイプライン
データクレンジングスクリプト
3スタイルのCSVを正規化し cleaned_reservations_202401.csv を出力する
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# 列名マッピング: スタイル別 -> 正規名
COLUMN_MAP = {
    # スタイルA: 標準日本語
    "予約日": "reserv_date",
    "予約番号": "reserv_no",
    "店舗名": "store_name",
    "コース": "course",
    "予約人数": "guest_count",
    "予約金額": "amount",
    "ステータス": "status",
    "キャンセル理由": "cancel_reason",
    # スタイルB: 英語
    "ReservDate": "reserv_date",
    "ReservNo": "reserv_no",
    "StoreName": "store_name",
    "Course": "course",
    "GuestCount": "guest_count",
    "Amount": "amount",
    "Status": "status",
    "CancelReason": "cancel_reason",
    # スタイルC: バリアント日本語
    "日付": "reserv_date",
    "管理番号": "reserv_no",
    "店舗": "store_name",
    "コース区分": "course",
    "人数": "guest_count",
    "金額": "amount",
    "状態": "status",
    "理由": "cancel_reason",
}

CANONICAL_COLUMNS = [
    "reserv_date",
    "reserv_no",
    "store_name",
    "course",
    "guest_count",
    "amount",
    "status",
    "cancel_reason",
]

WEEKDAY_MAP = {0: "月", 1: "火", 2: "水", 3: "木", 4: "金", 5: "土", 6: "日"}


def normalize_date(series: pd.Series) -> pd.Series:
    """スラッシュをダッシュに変換してから datetime にパースし YYYY-MM-DD 文字列で返す"""
    converted = series.astype(str).str.replace("/", "-", regex=False)
    return pd.to_datetime(converted, format="%Y-%m-%d").dt.strftime("%Y-%m-%d")


def load_and_normalize(filepath: Path) -> pd.DataFrame:
    """CSVを読み込み、列名を正規化して返す"""
    df = pd.read_csv(filepath, encoding="utf-8-sig", dtype=str)
    df = df.rename(columns=COLUMN_MAP)
    # 正規列だけ残す
    available = [c for c in CANONICAL_COLUMNS if c in df.columns]
    df = df[available].copy()
    df["source_file"] = filepath.name
    return df


def add_computed_columns(df: pd.DataFrame) -> pd.DataFrame:
    """計算列を追加する"""
    # 日付正規化
    df["reserv_date"] = normalize_date(df["reserv_date"])

    # 数値変換
    df["guest_count"] = pd.to_numeric(df["guest_count"], errors="coerce").fillna(0).astype(int)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0).astype(int)

    # cancel_reason の空文字列を None 相当の NaN に
    df["cancel_reason"] = df["cancel_reason"].replace("", None)

    # is_cancel
    df["is_cancel"] = (df["status"] == "キャンセル").astype(int)

    # loss_amount: キャンセル時のみ金額をロス計上
    df["loss_amount"] = df.apply(
        lambda row: row["amount"] if row["is_cancel"] == 1 else 0, axis=1
    )

    # day_of_week
    df["day_of_week"] = pd.to_datetime(df["reserv_date"]).dt.dayofweek.map(WEEKDAY_MAP)

    return df


def main():
    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {DATA_DIR}")

    frames = []
    for fp in csv_files:
        df = load_and_normalize(fp)
        frames.append(df)
        print(f"[OK] Loaded: {fp.name} ({len(df)} rows)")

    combined = pd.concat(frames, ignore_index=True)
    combined = add_computed_columns(combined)

    output_path = OUTPUT_DIR / "cleaned_reservations_202401.csv"
    combined.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[OK] Output: {output_path} ({len(combined)} rows)")
    return combined


if __name__ == "__main__":
    main()

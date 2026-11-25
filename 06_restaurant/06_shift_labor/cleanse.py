# -*- coding: utf-8 -*-
"""
C-40: アルバイトシフト管理・人件費集計パイプライン
データクレンジングスクリプト
3スタイルのCSVを読み込み、統一正規化して output/cleaned_shift_202401.csv に出力
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ---- パス定義 ----
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "cleaned_shift_202401.csv"

# ---- 列名マッピング ----
COLUMN_MAP = {
    # スタイルA（標準日本語）
    "勤務日": "work_date",
    "スタッフID": "staff_id",
    "店舗名": "store_name",
    "役職": "role",
    "出勤時刻": "start_time",
    "退勤時刻": "end_time",
    "実働時間": "work_hours",
    "時給": "hourly_rate",
    # スタイルB（英語）
    "WorkDate": "work_date",
    "StaffID": "staff_id",
    "StoreName": "store_name",
    "Role": "role",
    "StartTime": "start_time",
    "EndTime": "end_time",
    "WorkHours": "work_hours",
    "HourlyRate": "hourly_rate",
    # スタイルC（バリアント日本語）
    "日付": "work_date",
    "従業員番号": "staff_id",
    "店舗": "store_name",
    "ポジション": "role",
    "開始": "start_time",
    "終了": "end_time",
    "勤務時間": "work_hours",
    "時給単価": "hourly_rate",
}

REQUIRED_COLS = [
    "work_date", "staff_id", "store_name", "role",
    "start_time", "end_time", "work_hours", "hourly_rate",
]


def load_and_rename(filepath: Path) -> pd.DataFrame:
    """CSVを読み込み、列名を正規名にリネームして source_file 列を付与"""
    df = pd.read_csv(filepath, encoding="utf-8-sig", dtype=str)
    df = df.rename(columns=COLUMN_MAP)
    df["source_file"] = filepath.name
    return df


def normalize_date(series: pd.Series) -> pd.Series:
    """日付を YYYY-MM-DD に統一（スラッシュをダッシュに先に変換）"""
    normalized = series.str.replace("/", "-", regex=False)
    return pd.to_datetime(normalized, format="%Y-%m-%d", errors="coerce").dt.strftime("%Y-%m-%d")


def add_calculated_columns(df: pd.DataFrame) -> pd.DataFrame:
    """計算列を追加"""
    df["work_hours"] = pd.to_numeric(df["work_hours"], errors="coerce")
    df["hourly_rate"] = pd.to_numeric(df["hourly_rate"], errors="coerce")

    # 日次賃金
    df["daily_wage"] = df["work_hours"] * df["hourly_rate"]

    # 残業フラグ（8時間超）
    df["is_overtime"] = (df["work_hours"] > 8).astype(int)

    # 高コストフラグ（75パーセンタイル超）
    p75 = df["daily_wage"].quantile(0.75)
    df["labor_cost_flag"] = df["daily_wage"].apply(
        lambda x: "高コスト" if x > p75 else "標準"
    )

    return df


def cleanse() -> pd.DataFrame:
    """全CSVを読み込み、クレンジングして返す"""
    csv_files = sorted(DATA_DIR.glob("shift_style*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"CSVファイルが見つかりません: {DATA_DIR}")

    frames = []
    for filepath in csv_files:
        df = load_and_rename(filepath)
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)

    # 必須列の確認
    missing = [c for c in REQUIRED_COLS if c not in combined.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {missing}")

    # 日付正規化
    combined["work_date"] = normalize_date(combined["work_date"])

    # 計算列追加
    combined = add_calculated_columns(combined)

    # 欠損行の削除（必須列のいずれかが欠損）
    combined = combined.dropna(subset=REQUIRED_COLS)

    return combined


def main():
    print("[INFO] クレンジング開始 ...")
    df = cleanse()
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"[OK] クレンジング完了: {len(df)} 行 -> {OUTPUT_FILE}")
    print(f"[INFO] 残業シフト数: {df['is_overtime'].sum()} 件")
    print(f"[INFO] 高コストシフト数: {(df['labor_cost_flag'] == '高コスト').sum()} 件")


if __name__ == "__main__":
    main()

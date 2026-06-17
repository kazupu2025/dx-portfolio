# -*- coding: utf-8 -*-
"""
C-37: 来客記録データ集計・スループット分析パイプライン
クレンジングスクリプト: 3スタイルのCSVを統一正規化して output/cleaned_reception_202401.csv に出力する
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================
# 列名マッピング（スタイルA / B / C -> 正規名）
# ============================================================
COLUMN_MAP = [
    # スタイルA: 標準日本語
    {
        "来院日": "visit_date",
        "受付番号": "reception_no",
        "診療科": "department",
        "来院時刻": "arrival_time",
        "診察開始時刻": "start_time",
        "診察終了時刻": "end_time",
        "待ち時間（分）": "wait_minutes",
        "診察時間（分）": "treat_minutes",
    },
    # スタイルB: 英語
    {
        "VisitDate": "visit_date",
        "ReceptionNo": "reception_no",
        "Department": "department",
        "ArrivalTime": "arrival_time",
        "StartTime": "start_time",
        "EndTime": "end_time",
        "WaitMinutes": "wait_minutes",
        "TreatMinutes": "treat_minutes",
    },
    # スタイルC: バリアント日本語
    {
        "日付": "visit_date",
        "整理番号": "reception_no",
        "科名": "department",
        "受付時刻": "arrival_time",
        "開始時刻": "start_time",
        "終了時刻": "end_time",
        "待機分": "wait_minutes",
        "診療分": "treat_minutes",
    },
]

REQUIRED_COLS = [
    "visit_date", "reception_no", "department",
    "arrival_time", "start_time", "end_time",
    "wait_minutes", "treat_minutes",
]


def detect_and_rename(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    """列名を検出してリネームし、source_file 列を付与する"""
    for mapping in COLUMN_MAP:
        if set(mapping.keys()).issubset(set(df.columns)):
            df = df.rename(columns=mapping)
            df["source_file"] = source_file
            return df
    raise ValueError(f"Unknown column format in {source_file}. Columns: {list(df.columns)}")


def parse_date(series: pd.Series) -> pd.Series:
    """YYYY/MM/DD または YYYY-MM-DD を YYYY-MM-DD に統一"""
    normalized = series.str.replace("/", "-", regex=False)
    return pd.to_datetime(normalized, format="%Y-%m-%d").dt.strftime("%Y-%m-%d")


def compute_time_slot(arrival_time_str: str) -> str:
    """arrival_timeの時刻から 'HH-HH時' の形式で時間帯を算出"""
    try:
        hour = int(str(arrival_time_str).split(":")[0])
        return f"{hour:02d}-{hour + 1:02d}時"
    except (ValueError, IndexError, AttributeError):
        return "不明"


def compute_wait_level(wait_min) -> str:
    """待ち時間レベルを算出"""
    try:
        w = float(wait_min)
        if w > 60:
            return "長待ち"
        elif w > 30:
            return "普通"
        else:
            return "短待ち"
    except (ValueError, TypeError):
        return "普通"


def load_all_csvs() -> pd.DataFrame:
    """data/ フォルダ内のすべての CSV を読み込んで結合する"""
    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {DATA_DIR}")

    frames = []
    for path in csv_files:
        df = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
        df = detect_and_rename(df, path.name)
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    return combined


def cleanse() -> pd.DataFrame:
    df = load_all_csvs()

    # 日付正規化（スラッシュをダッシュに変換してからto_datetime）
    df["visit_date"] = parse_date(df["visit_date"])

    # 数値列変換
    df["wait_minutes"] = pd.to_numeric(df["wait_minutes"], errors="coerce")
    df["treat_minutes"] = pd.to_numeric(df["treat_minutes"], errors="coerce")

    # 重複除去
    df = df.drop_duplicates()

    # 計算列: wait_level
    df["wait_level"] = df["wait_minutes"].apply(compute_wait_level)

    # 計算列: time_slot
    df["time_slot"] = df["arrival_time"].apply(compute_time_slot)

    # 列順
    output_cols = REQUIRED_COLS + ["source_file", "wait_level", "time_slot"]
    df = df[output_cols]

    # 出力
    out_path = OUTPUT_DIR / "cleaned_reception_202401.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[OK] クレンジング完了: {len(df)} 件 -> {out_path}")
    return df


if __name__ == "__main__":
    cleanse()

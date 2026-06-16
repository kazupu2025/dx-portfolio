# -*- coding: utf-8 -*-
"""
C-25: 生産計画 vs 実績 差異分析パイプライン
クレンジングスクリプト

3スタイルのCSVを統一正規化し、計算列を追加して出力する。
"""
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# 3スタイルの列名マッピング -> 正規名
COLUMN_MAP = {
    # スタイルA（標準日本語）
    "日付": "date",
    "ライン名": "line_name",
    "製品カテゴリ": "category",
    "計画数量": "planned_qty",
    "実績数量": "actual_qty",
    "不良数": "defect_qty",
    "作業時間": "work_hours",
    # スタイルB（英語）
    "Date": "date",
    "LineName": "line_name",
    "Category": "category",
    "PlannedQty": "planned_qty",
    "ActualQty": "actual_qty",
    "DefectQty": "defect_qty",
    "WorkHours": "work_hours",
    # スタイルC（バリアント日本語）
    "集計日": "date",
    "製造ライン": "line_name",
    "品種": "category",
    "目標生産数": "planned_qty",
    "生産実績数": "actual_qty",
    "不良品数": "defect_qty",
    "稼働時間": "work_hours",
}

REQUIRED_COLS = ["date", "line_name", "category", "planned_qty", "actual_qty", "defect_qty", "work_hours"]


def normalize_date(series: pd.Series) -> pd.Series:
    """YYYY/MM/DD と YYYY-MM-DD を YYYY-MM-DD に統一"""
    return pd.to_datetime(series, format="mixed", dayfirst=False).dt.strftime("%Y-%m-%d")


def load_and_normalize(csv_path: Path) -> pd.DataFrame:
    """1ファイルを読み込み、列名を正規名に変換する"""
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    # 列名をマッピング（該当しない列はそのまま）
    df = df.rename(columns=COLUMN_MAP)
    # 必須列の存在確認
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"{csv_path.name}: 必須列が見つかりません: {missing}")
    df = df[REQUIRED_COLS].copy()
    df["source_file"] = csv_path.name
    return df


def add_calculated_columns(df: pd.DataFrame) -> pd.DataFrame:
    """計算列を追加"""
    # 数値型に変換
    for col in ["planned_qty", "actual_qty", "defect_qty", "work_hours"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 達成率: actual / planned（0除算はNaN）
    df["achievement_rate"] = df.apply(
        lambda r: r["actual_qty"] / r["planned_qty"] if r["planned_qty"] != 0 else float("nan"),
        axis=1,
    )

    # 不良率: defect / actual（0除算はNaN）
    df["defect_rate"] = df.apply(
        lambda r: r["defect_qty"] / r["actual_qty"] if r["actual_qty"] != 0 else float("nan"),
        axis=1,
    )

    # 差異数量: actual - planned
    df["variance_qty"] = df["actual_qty"] - df["planned_qty"]

    # 達成フラグ
    df["achievement_flag"] = df["achievement_rate"].apply(
        lambda x: "達成" if (pd.notna(x) and x >= 1.0) else "未達"
    )

    return df


def cleanse() -> pd.DataFrame:
    """全CSVを読み込み、クレンジングして結合し、出力する"""
    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"data/ フォルダにCSVファイルが見つかりません: {DATA_DIR}")

    frames = []
    for f in csv_files:
        print(f"[OK] Loading: {f.name}")
        df = load_and_normalize(f)
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    combined["date"] = normalize_date(combined["date"])
    combined = add_calculated_columns(combined)

    out_path = OUTPUT_DIR / "cleaned_production_202401.csv"
    combined.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[OK] Output: {out_path} ({len(combined)} rows)")
    return combined


if __name__ == "__main__":
    cleanse()

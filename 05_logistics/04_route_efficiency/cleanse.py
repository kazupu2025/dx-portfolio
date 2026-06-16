# -*- coding: utf-8 -*-
"""
データクレンジングスクリプト
3スタイルのCSVを統一正規化して output/cleaned_route_202401.csv に出力する
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# 各スタイルの列名マッピング
COLUMN_MAP = {
    # スタイルA: 標準日本語
    "運行日": "date",
    "ルートID": "route_id",
    "エリア": "area",
    "車両タイプ": "vehicle_type",
    "走行距離km": "distance_km",
    "所要時間分": "duration_min",
    "燃料費": "fuel_cost",
    "配送件数": "delivery_count",
    "遅延フラグ": "delay_flag",
    # スタイルB: 英語
    "Date": "date",
    "RouteID": "route_id",
    "Area": "area",
    "VehicleType": "vehicle_type",
    "DistanceKm": "distance_km",
    "DurationMin": "duration_min",
    "FuelCost": "fuel_cost",
    "DeliveryCount": "delivery_count",
    "DelayFlag": "delay_flag",
    # スタイルC: バリアント日本語
    "日付": "date",
    "路線CD": "route_id",
    "担当エリア": "area",
    "車種": "vehicle_type",
    "走行km": "distance_km",
    "所要分": "duration_min",
    "燃油費": "fuel_cost",
    "件数": "delivery_count",
    "遅延": "delay_flag",
}

REQUIRED_COLS = [
    "date", "route_id", "area", "vehicle_type",
    "distance_km", "duration_min", "fuel_cost",
    "delivery_count", "delay_flag"
]


def normalize_date(series: pd.Series) -> pd.Series:
    """日付列を YYYY-MM-DD 形式に統一する"""
    def _parse(val):
        val = str(val).strip()
        for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y%m%d"):
            try:
                return pd.to_datetime(val, format=fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        try:
            return pd.to_datetime(val).strftime("%Y-%m-%d")
        except Exception:
            return np.nan
    return series.apply(_parse)


def load_and_rename(filepath: Path) -> pd.DataFrame:
    """CSVを読み込み、列名を正規名に変換する"""
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    df = df.rename(columns=COLUMN_MAP)
    df["source_file"] = filepath.name
    return df


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """計算列を追加する"""
    df["distance_km"] = pd.to_numeric(df["distance_km"], errors="coerce")
    df["fuel_cost"] = pd.to_numeric(df["fuel_cost"], errors="coerce")
    df["delivery_count"] = pd.to_numeric(df["delivery_count"], errors="coerce")

    # 0除算は NaN
    df["cost_per_km"] = np.where(
        df["distance_km"] > 0,
        df["fuel_cost"] / df["distance_km"],
        np.nan
    )
    df["cost_per_delivery"] = np.where(
        df["delivery_count"] > 0,
        df["fuel_cost"] / df["delivery_count"],
        np.nan
    )
    df["km_per_delivery"] = np.where(
        df["delivery_count"] > 0,
        df["distance_km"] / df["delivery_count"],
        np.nan
    )

    # efficiency_flag: cost_per_delivery の中央値より小さければ高効率
    median_cpd = df["cost_per_delivery"].median()
    df["efficiency_flag"] = np.where(
        df["cost_per_delivery"] < median_cpd,
        "高効率",
        "低効率"
    )

    return df


def normalize_delay_flag(df: pd.DataFrame) -> pd.DataFrame:
    """delay_flag を int (0/1) に正規化する"""
    def _to_int(val):
        if isinstance(val, bool):
            return int(val)
        try:
            v = int(float(str(val).strip()))
            return 1 if v != 0 else 0
        except (ValueError, TypeError):
            return 0
    df["delay_flag"] = df["delay_flag"].apply(_to_int)
    return df


def main():
    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if not csv_files:
        print("[ERROR] data/ フォルダに CSV ファイルが見つかりません。")
        return

    dfs = []
    for fp in csv_files:
        print(f"[LOAD] {fp.name}")
        df = load_and_rename(fp)
        # 正規列のみ保持（存在するものだけ）
        cols_present = [c for c in REQUIRED_COLS if c in df.columns]
        df = df[cols_present + ["source_file"]]
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)

    # 日付正規化
    combined["date"] = normalize_date(combined["date"])

    # delay_flag 正規化
    combined = normalize_delay_flag(combined)

    # 計算列追加
    combined = add_derived_columns(combined)

    # 出力
    out_path = OUTPUT_DIR / "cleaned_route_202401.csv"
    combined.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[DONE] クレンジング完了: {len(combined)}行 -> {out_path}")


if __name__ == "__main__":
    main()

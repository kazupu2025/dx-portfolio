"""
C-17 配送コスト分析パイプライン
データクレンジングスクリプト
全CSVを読み込み、列名を正規化して output/cleaned_delivery_202401.csv を出力する
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    # delivery_id
    "配送ID": "delivery_id", "delivery_id": "delivery_id", "伝票番号": "delivery_id",
    # date
    "日付": "date", "date": "date", "集計日": "date",
    # route_id
    "ルートID": "route_id", "route_id": "route_id", "路線": "route_id",
    # vehicle_type
    "車種": "vehicle_type", "vehicle_type": "vehicle_type", "車両種別": "vehicle_type",
    # distance_km
    "距離km": "distance_km", "distance_km": "distance_km", "走行距離": "distance_km",
    # fuel_cost
    "燃料費": "fuel_cost", "fuel_cost": "fuel_cost", "燃費費用": "fuel_cost",
    # toll_cost
    "高速代": "toll_cost", "toll_cost": "toll_cost", "道路料金": "toll_cost",
    # driver_cost
    "ドライバー人件費": "driver_cost", "driver_cost": "driver_cost", "人件費": "driver_cost",
    # cargo_weight_kg
    "積載重量kg": "cargo_weight_kg", "cargo_weight_kg": "cargo_weight_kg", "荷重": "cargo_weight_kg",
    # delivery_count
    "配送件数": "delivery_count", "delivery_count": "delivery_count", "件数": "delivery_count",
    # status
    "配送ステータス": "status", "status": "status", "状態": "status",
}

STATUS_MAP = {
    "完了": "完了", "完了済": "完了", "Completed": "完了",
    "遅延": "遅延", "Delayed": "遅延",
    "キャンセル": "キャンセル", "Cancelled": "キャンセル",
}

NUMERIC_COLS = ["fuel_cost", "toll_cost", "driver_cost", "distance_km", "cargo_weight_kg", "delivery_count"]
CANONICAL_COLS = ["delivery_id", "date", "route_id", "vehicle_type", "distance_km",
                  "fuel_cost", "toll_cost", "driver_cost", "cargo_weight_kg", "delivery_count", "status"]


def load_and_rename(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    rename_map = {col: COLUMN_MAP[col] for col in df.columns if col in COLUMN_MAP}
    df = df.rename(columns=rename_map)
    df["source_file"] = path.name
    return df


def normalize_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.strftime("%Y-%m-%d")


def fill_numeric(df: pd.DataFrame) -> pd.DataFrame:
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
    return df


def normalize_status(series: pd.Series) -> pd.Series:
    return series.map(lambda x: STATUS_MAP.get(str(x).strip(), x))


def main():
    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {DATA_DIR}")

    dfs = []
    for f in csv_files:
        df = load_and_rename(f)
        dfs.append(df)
        print(f"  Loaded: {f.name} ({len(df)} rows)")

    combined = pd.concat(dfs, ignore_index=True)
    print(f"\n[合計] {len(combined)} rows from {len(dfs)} files")

    # 列が存在しない場合のフォールバック
    for col in CANONICAL_COLS:
        if col not in combined.columns:
            combined[col] = np.nan

    # 日付正規化
    combined["date"] = normalize_date(combined["date"])

    # 数値補完
    combined = fill_numeric(combined)

    # 派生列
    combined["total_cost"] = combined["fuel_cost"] + combined["toll_cost"] + combined["driver_cost"]
    combined["cost_per_km"] = np.where(
        combined["distance_km"] > 0,
        combined["total_cost"] / combined["distance_km"],
        np.nan
    )
    combined["cost_per_delivery"] = np.where(
        combined["delivery_count"] > 0,
        combined["total_cost"] / combined["delivery_count"],
        np.nan
    )

    # ステータス正規化
    combined["status"] = normalize_status(combined["status"])

    # 出力列順序
    output_cols = CANONICAL_COLS + ["total_cost", "cost_per_km", "cost_per_delivery", "source_file"]
    # 余分な列を除外し、存在する列だけ選択
    output_cols = [c for c in output_cols if c in combined.columns]
    combined = combined[output_cols]

    out_path = OUTPUT_DIR / "cleaned_delivery_202401.csv"
    combined.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n[OK] Output: {out_path} ({len(combined)} rows)")


if __name__ == "__main__":
    main()

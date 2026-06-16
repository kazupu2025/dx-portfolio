"""
C-22 ドライバー勤怠・拘束時間管理パイプライン
データクレンジングスクリプト
全CSVを読み込み、列名を正規化して output/cleaned_driver_202401.csv を出力する
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    "ドライバーID": "driver_id", "driver_id": "driver_id", "社員番号": "driver_id",
    "氏名": "name", "name": "name", "運転者名": "name",
    "営業所": "office", "office": "office", "所属": "office",
    "乗務日": "work_date", "work_date": "work_date", "乗務日付": "work_date",
    "出庫時刻": "departure_time", "departure_time": "departure_time", "出発時刻": "departure_time",
    "帰庫時刻": "return_time", "return_time": "return_time", "到着時刻": "return_time",
    "休憩時間h": "break_hours", "break_hours": "break_hours", "休憩h": "break_hours",
    "走行距離km": "distance_km", "distance_km": "distance_km", "走行km": "distance_km",
    "運行区分": "operation_type", "operation_type": "operation_type", "運行種別": "operation_type",
}

NUMERIC_COLS = ["break_hours", "distance_km"]

CANONICAL_COLS = [
    "driver_id", "name", "office", "work_date",
    "departure_time", "return_time",
    "break_hours", "distance_km", "operation_type",
]


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


def calc_confinement_hours(row: pd.Series) -> float:
    """帰庫時刻 - 出庫時刻 の時間差（時間単位）"""
    try:
        dep = pd.to_datetime(f"2024-01-01 {row['departure_time']}", format="%Y-%m-%d %H:%M")
        ret = pd.to_datetime(f"2024-01-01 {row['return_time']}", format="%Y-%m-%d %H:%M")
        if ret <= dep:
            ret += pd.Timedelta(days=1)
        diff = (ret - dep).total_seconds() / 3600
        return round(diff, 2)
    except Exception:
        return np.nan


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

    # 必須列が存在しない場合フォールバック
    for col in CANONICAL_COLS:
        if col not in combined.columns:
            combined[col] = np.nan

    # 日付正規化
    combined["work_date"] = normalize_date(combined["work_date"])

    # 数値補完
    combined = fill_numeric(combined)

    # 拘束時間・実労働時間の計算
    combined["confinement_hours"] = combined.apply(calc_confinement_hours, axis=1)
    combined["work_hours"] = (combined["confinement_hours"] - combined["break_hours"]).round(2)

    # 違反フラグ
    combined["confinement_over_flag"] = combined["confinement_hours"] > 13
    combined["work_over_flag"] = combined["work_hours"] > 9
    combined["violation_flag"] = combined.apply(
        lambda r: "違反" if r["confinement_over_flag"] or r["work_over_flag"] else "正常",
        axis=1,
    )

    # 出力列順序
    output_cols = CANONICAL_COLS + [
        "confinement_hours", "work_hours",
        "confinement_over_flag", "work_over_flag", "violation_flag",
        "source_file",
    ]
    output_cols = [c for c in output_cols if c in combined.columns]
    combined = combined[output_cols]

    out_path = OUTPUT_DIR / "cleaned_driver_202401.csv"
    combined.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n[OK] Output: {out_path} ({len(combined)} rows)")


if __name__ == "__main__":
    main()

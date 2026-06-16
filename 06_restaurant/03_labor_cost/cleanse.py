"""
C-20: クレンジングスクリプト
data/ 以下の3スタイルCSVを統一フォーマットに変換し output/cleaned_labor_202401.csv へ出力
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    "スタッフID": "staff_id", "staff_id": "staff_id", "社員番号": "staff_id",
    "氏名": "name", "name": "name", "スタッフ名": "name",
    "店舗ID": "store_id", "store_id": "store_id", "店番": "store_id",
    "雇用区分": "employment_type", "employment_type": "employment_type", "雇用形態": "employment_type",
    "時給": "hourly_wage", "hourly_wage": "hourly_wage", "賃金": "hourly_wage",
    "勤務日": "work_date", "work_date": "work_date", "日付": "work_date",
    "出勤時刻": "clock_in", "clock_in": "clock_in", "開始時刻": "clock_in",
    "退勤時刻": "clock_out", "clock_out": "clock_out", "終了時刻": "clock_out",
    "休憩分": "break_minutes", "break_minutes": "break_minutes", "休憩時間": "break_minutes",
    "実働時間": "work_hours", "work_hours": "work_hours", "勤務時間": "work_hours",
    "深夜区分": "late_night", "late_night": "late_night", "深夜勤務": "late_night",
}

REQUIRED_COLS = [
    "staff_id", "name", "store_id", "employment_type", "hourly_wage",
    "work_date", "clock_in", "clock_out", "break_minutes", "work_hours", "late_night",
]


def read_csv_auto(path: Path) -> pd.DataFrame:
    """エンコーディング自動検出してCSV読み込み"""
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            raw.decode(enc)
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path)


def normalize_date(val) -> str | None:
    """YYYY-MM-DD 形式に正規化"""
    if pd.isna(val):
        return None
    s = str(val).strip()
    for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y年%m月%d日"):
        try:
            return pd.to_datetime(s, format=fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    try:
        return pd.to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        return None


def normalize_bool(val) -> bool:
    """late_night を bool に統一"""
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    s = str(val).strip().lower()
    return s in ("true", "1", "yes", "深夜あり", "深夜")


def process_file(path: Path) -> pd.DataFrame:
    df = read_csv_auto(path)

    # 列名マッピング
    renamed = {col: COLUMN_MAP[str(col).strip()] for col in df.columns if str(col).strip() in COLUMN_MAP}
    df = df.rename(columns=renamed)

    # source_file 列追加
    df["source_file"] = path.name

    # 不要列削除
    keep = [c for c in REQUIRED_COLS + ["source_file"] if c in df.columns]
    df = df[keep]

    # 全列 NaN 行削除
    df = df.dropna(how="all")

    # work_date 正規化
    if "work_date" in df.columns:
        df["work_date"] = df["work_date"].apply(normalize_date)
        df = df.dropna(subset=["work_date"])

    # hourly_wage: 欠損を中央値で補完
    if "hourly_wage" in df.columns:
        df["hourly_wage"] = pd.to_numeric(df["hourly_wage"], errors="coerce")
        median_wage = df["hourly_wage"].median()
        df["hourly_wage"] = df["hourly_wage"].fillna(median_wage if pd.notna(median_wage) else 1100)
        df["hourly_wage"] = df["hourly_wage"].clip(lower=0)
    else:
        df["hourly_wage"] = 1100.0

    # work_hours: 欠損を 0 で補完
    if "work_hours" in df.columns:
        df["work_hours"] = pd.to_numeric(df["work_hours"], errors="coerce").fillna(0).clip(lower=0)
    else:
        df["work_hours"] = 0.0

    # break_minutes: 欠損を 0 で補完
    if "break_minutes" in df.columns:
        df["break_minutes"] = pd.to_numeric(df["break_minutes"], errors="coerce").fillna(0).clip(lower=0)
    else:
        df["break_minutes"] = 0.0

    # late_night を bool に統一
    if "late_night" in df.columns:
        df["late_night"] = df["late_night"].apply(normalize_bool)
    else:
        df["late_night"] = False

    # 計算列
    df["base_wage"] = (df["hourly_wage"] * df["work_hours"]).round(2)
    df["late_night_premium"] = (df["base_wage"] * 0.25 * df["late_night"].astype(int)).round(2)
    df["total_wage"] = (df["base_wage"] + df["late_night_premium"]).round(2)
    df["overtime_hours"] = (df["work_hours"] - 8).clip(lower=0).round(2)

    return df


def main():
    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if not csv_files:
        print(f"データファイルが見つかりません: {DATA_DIR}")
        return

    frames = []
    for path in csv_files:
        print(f"処理中: {path.name}")
        df = process_file(path)
        frames.append(df)
        print(f"  -> {len(df)} 行")

    result = pd.concat(frames, ignore_index=True)
    result = result.drop_duplicates()

    col_order = [
        "staff_id", "name", "store_id", "employment_type",
        "hourly_wage", "work_date", "clock_in", "clock_out",
        "break_minutes", "work_hours", "late_night",
        "base_wage", "late_night_premium", "total_wage", "overtime_hours",
        "source_file",
    ]
    result = result[[c for c in col_order if c in result.columns]]

    out_path = OUTPUT_DIR / "cleaned_labor_202401.csv"
    result.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\nクレンジング完了: {len(result)} 行")
    print(f"出力: {out_path}")
    print(f"列: {list(result.columns)}")


if __name__ == "__main__":
    main()

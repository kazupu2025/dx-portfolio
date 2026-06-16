"""
C-19: cleanse.py
data/ 配下の全CSVを読み込み、列名統一・計算列追加・クレンジングを行い
output/cleaned_pnl_202401.csv を出力する
"""
import os
import sys
import re
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "cleaned_pnl_202401.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)

COLUMN_MAP = {
    "店舗ID": "store_id", "store_id": "store_id", "店番": "store_id",
    "店舗名": "store_name", "store_name": "store_name", "店舗": "store_name",
    "年月": "year_month", "year_month": "year_month", "期間": "year_month",
    "売上予算": "planned_revenue", "planned_revenue": "planned_revenue", "売上計画": "planned_revenue",
    "売上実績": "actual_revenue", "actual_revenue": "actual_revenue",
    "原価予算": "planned_cogs", "planned_cogs": "planned_cogs", "売上原価計画": "planned_cogs",
    "原価実績": "actual_cogs", "actual_cogs": "actual_cogs", "売上原価実績": "actual_cogs",
    "人件費予算": "planned_labor", "planned_labor": "planned_labor", "人件費計画": "planned_labor",
    "人件費実績": "actual_labor", "actual_labor": "actual_labor",
    "その他費用予算": "planned_other", "planned_other": "planned_other", "諸経費計画": "planned_other",
    "その他費用実績": "actual_other", "actual_other": "actual_other", "諸経費実績": "actual_other",
}

NUMERIC_COLS = [
    "planned_revenue", "actual_revenue",
    "planned_cogs", "actual_cogs",
    "planned_labor", "actual_labor",
    "planned_other", "actual_other",
]


def normalize_year_month(val):
    """year_month を YYYY-WNN 形式（週次）または YYYY-MM 形式に正規化する"""
    s = str(val).strip()
    # 週次: 2024-W01, 2024-W1, 2024W01 など
    m = re.match(r"(\d{4})[_\-\s]?W(\d{1,2})$", s, re.IGNORECASE)
    if m:
        return f"{m.group(1)}-W{m.group(2).zfill(2)}"
    # 月次: 2024-01, 202401, 2024/01 など
    m2 = re.match(r"(\d{4})[/\-_]?(\d{2})$", s)
    if m2:
        return f"{m2.group(1)}-{m2.group(2)}"
    return s


def load_csvs():
    frames = []
    csv_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".csv")])
    if not csv_files:
        print(f"[ERROR] No CSV files found in {DATA_DIR}", file=sys.stderr)
        sys.exit(1)

    for fname in csv_files:
        path = os.path.join(DATA_DIR, fname)
        try:
            df = pd.read_csv(path, encoding="utf-8-sig")
        except UnicodeDecodeError:
            df = pd.read_csv(path, encoding="cp932")

        # 列名統一
        df.rename(columns=COLUMN_MAP, inplace=True)

        # source_file 列追加
        df["source_file"] = fname

        frames.append(df)
        print(f"  Loaded: {fname} ({len(df)} rows, {list(df.columns)})")

    return pd.concat(frames, ignore_index=True)


def add_computed_columns(df):
    """計算列を追加する"""
    df["planned_gross_profit"] = df["planned_revenue"] - df["planned_cogs"]
    df["actual_gross_profit"] = df["actual_revenue"] - df["actual_cogs"]

    df["planned_operating_profit"] = (
        df["planned_gross_profit"] - df["planned_labor"] - df["planned_other"]
    )
    df["actual_operating_profit"] = (
        df["actual_gross_profit"] - df["actual_labor"] - df["actual_other"]
    )

    df["revenue_variance"] = df["actual_revenue"] - df["planned_revenue"]
    df["revenue_variance_ratio"] = df["revenue_variance"] / df["planned_revenue"]

    df["profit_variance"] = df["actual_operating_profit"] - df["planned_operating_profit"]
    # 分母0ならNaN
    df["profit_variance_ratio"] = df.apply(
        lambda row: (
            row["profit_variance"] / row["planned_operating_profit"]
            if row["planned_operating_profit"] != 0
            else float("nan")
        ),
        axis=1,
    )

    def calc_profit_flag(op):
        if op < 0:
            return "赤字"
        return "達成"

    # 未達: 実績が計画の90%未満
    def calc_flag(row):
        op = row["actual_operating_profit"]
        planned_op = row["planned_operating_profit"]
        if op < 0:
            return "赤字"
        if planned_op > 0 and op < planned_op * 0.9:
            return "未達"
        return "達成"

    df["profit_flag"] = df.apply(calc_flag, axis=1)
    return df


def main():
    print("[cleanse.py] Loading CSV files...")
    df = load_csvs()
    print(f"  Total rows loaded: {len(df)}")

    # 列名統一済み確認
    missing = [c for c in ["store_id", "store_name", "year_month"] + NUMERIC_COLS if c not in df.columns]
    if missing:
        print(f"[ERROR] Missing columns after mapping: {missing}", file=sys.stderr)
        sys.exit(1)

    # year_month 正規化
    df["year_month"] = df["year_month"].apply(normalize_year_month)

    # 数値列の欠損を中央値補完
    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        median_val = df[col].median()
        n_missing = df[col].isna().sum()
        if n_missing > 0:
            print(f"  Filling {n_missing} missing values in '{col}' with median={median_val}")
        df[col] = df[col].fillna(median_val)

    # 計算列追加
    df = add_computed_columns(df)

    # 出力
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"[cleanse.py] Done. Output: {OUTPUT_FILE} ({len(df)} rows)")


if __name__ == "__main__":
    main()

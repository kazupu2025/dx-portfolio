"""
C-21: サービス別売上・原価分析パイプライン
データクレンジングスクリプト
data/ の全CSVを読み込み、統一フォーマットに変換して output/ に出力する
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).parent
DATA_DIR = BASE / "data"
OUTPUT_DIR = BASE / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "cleaned_revenue_cost_202401.csv"

COLUMN_MAP = {
    "案件ID": "project_id", "project_id": "project_id", "プロジェクトID": "project_id",
    "顧客名": "client_name", "client_name": "client_name", "クライアント": "client_name",
    "サービス区分": "service_type", "service_type": "service_type", "種別": "service_type",
    "担当部門": "department", "department": "department", "部署": "department",
    "契約月": "contract_month", "contract_month": "contract_month", "月度": "contract_month",
    "売上金額": "revenue", "revenue": "revenue", "売上高": "revenue",
    "直接原価": "direct_cost", "direct_cost": "direct_cost", "直接費": "direct_cost",
    "間接原価配賦": "allocated_overhead", "allocated_overhead": "allocated_overhead", "間接費": "allocated_overhead",
    "担当者工数h": "hours_spent", "hours_spent": "hours_spent", "工数": "hours_spent",
    "完了フラグ": "is_completed", "is_completed": "is_completed", "完了": "is_completed",
}

# 英語サービス区分を日本語に統一
SERVICE_TYPE_MAP = {
    "SaaS": "SaaS利用料",
    "Custom Development": "受託開発",
    "Maintenance Support": "保守サポート",
    "Consulting": "コンサルティング",
    "Training": "研修・教育",
}

# 英語部門名を日本語に統一
DEPARTMENT_MAP = {
    "Development": "開発部",
    "Sales": "営業部",
    "CS": "CS部",
    # "Consulting"は英語でもコンサルティングと紛らわしいので残す
}

NUMERIC_COLS = ["revenue", "direct_cost", "allocated_overhead", "hours_spent"]


def normalize_contract_month(val):
    """contract_month を YYYY-MM 形式に統一"""
    if pd.isna(val):
        return np.nan
    val = str(val).strip()
    # すでに YYYY-MM 形式
    if len(val) == 7 and val[4] == "-":
        return val
    # YYYY/MM 形式
    if len(val) == 7 and val[4] == "/":
        return val[:4] + "-" + val[5:]
    # YYYYMM 形式
    if len(val) == 6 and val.isdigit():
        return val[:4] + "-" + val[4:]
    return val


def normalize_is_completed(val):
    """is_completed をbool化"""
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        v = val.strip().lower()
        if v in ("true", "1", "完了", "yes", "y", "done"):
            return True
        if v in ("false", "0", "未完了", "no", "n", ""):
            return False
    return False


def load_and_merge():
    """data/ の全CSVを読み込み、カラム名を統一して結合"""
    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"data/ にCSVファイルが見つかりません: {DATA_DIR}")

    dfs = []
    for f in csv_files:
        df = pd.read_csv(f, encoding="utf-8-sig")
        # カラム名を統一
        df = df.rename(columns={c: COLUMN_MAP[c] for c in df.columns if c in COLUMN_MAP})
        df["source_file"] = f.name
        dfs.append(df)
        print(f"  読込: {f.name} ({len(df)}行)")

    merged = pd.concat(dfs, ignore_index=True)
    print(f"  結合後: {len(merged)}行")
    return merged


def cleanse(df: pd.DataFrame) -> pd.DataFrame:
    # 1. contract_month 正規化
    df["contract_month"] = df["contract_month"].apply(normalize_contract_month)

    # 2. service_type 英語→日本語統一
    df["service_type"] = df["service_type"].map(lambda x: SERVICE_TYPE_MAP.get(str(x).strip(), str(x).strip()) if pd.notna(x) else x)

    # 3. department 英語→日本語統一
    df["department"] = df["department"].map(lambda x: DEPARTMENT_MAP.get(str(x).strip(), str(x).strip()) if pd.notna(x) else x)

    # 4. 数値列の欠損を中央値補完
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)

    # 5. is_completed をbool化
    df["is_completed"] = df["is_completed"].apply(normalize_is_completed)

    # 6. 計算列追加
    df["total_cost"] = df["direct_cost"] + df["allocated_overhead"]
    df["gross_profit"] = df["revenue"] - df["direct_cost"]
    df["operating_profit"] = df["revenue"] - df["total_cost"]

    df["gross_margin_ratio"] = df.apply(
        lambda r: r["gross_profit"] / r["revenue"] if r["revenue"] != 0 else np.nan, axis=1
    )
    df["operating_margin_ratio"] = df.apply(
        lambda r: r["operating_profit"] / r["revenue"] if r["revenue"] != 0 else np.nan, axis=1
    )
    df["revenue_per_hour"] = df.apply(
        lambda r: r["revenue"] / r["hours_spent"] if r["hours_spent"] != 0 else np.nan, axis=1
    )

    def profit_flag(row):
        ratio = row["operating_margin_ratio"]
        if pd.isna(ratio):
            return "良好"
        if ratio < 0:
            return "赤字"
        if ratio < 0.10:
            return "低収益"
        return "良好"

    df["profit_flag"] = df.apply(profit_flag, axis=1)

    return df


def main():
    print("=== クレンジング開始 ===")
    df = load_and_merge()
    df = cleanse(df)

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\n[OK] {OUTPUT_FILE} に出力しました ({len(df)}行)")

    # サマリー
    print(f"\nservice_type: {sorted(df['service_type'].unique())}")
    print(f"department: {sorted(df['department'].unique())}")
    print(f"profit_flag: {df['profit_flag'].value_counts().to_dict()}")
    print(f"赤字件数: {(df['profit_flag'] == '赤字').sum()}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
C-58: クレンジングスクリプト
data/ 以下の3スタイルCSVを統一フォーマットに変換し output/cleaned_costs_202401.csv へ出力
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    # record_date
    "計上日": "record_date", "RecordDate": "record_date", "日付": "record_date",
    # record_id
    "記録ID": "record_id", "RecordID": "record_id", "管理番号": "record_id",
    # project_no
    "工事番号": "project_no", "ProjectNo": "project_no", "案件番号": "project_no",
    # work_type
    "工種": "work_type", "WorkType": "work_type", "作業区分": "work_type",
    # cost_category
    "費目": "cost_category", "CostCategory": "cost_category", "原価区分": "cost_category",
    # budget_amount
    "予算額": "budget_amount", "BudgetAmount": "budget_amount", "予定金額": "budget_amount",
    # actual_amount
    "実績額": "actual_amount", "ActualAmount": "actual_amount", "実際金額": "actual_amount",
    # is_over_budget
    "予算超過": "is_over_budget", "IsOverBudget": "is_over_budget", "オーバー": "is_over_budget",
}

CANONICAL_COLS = [
    "record_date",
    "record_id",
    "project_no",
    "work_type",
    "cost_category",
    "budget_amount",
    "actual_amount",
    "is_over_budget",
    "variance",
    "variance_rate",
    "budget_status",
    "variance_grade",
    "source_file",
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


def normalize_date(val) -> str:
    """YYYY-MM-DD 形式に正規化"""
    if pd.isna(val):
        return None
    s = str(val).strip().replace("/", "-")
    try:
        return pd.to_datetime(s, format="%Y-%m-%d").strftime("%Y-%m-%d")
    except Exception:
        pass
    try:
        return pd.to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        return None


def process_file(path: Path) -> pd.DataFrame:
    df = read_csv_auto(path)

    # 列名マッピング
    renamed = {col: COLUMN_MAP[str(col).strip()]
               for col in df.columns if str(col).strip() in COLUMN_MAP}
    df = df.rename(columns=renamed)

    # source_file 列追加
    df["source_file"] = path.name

    # 全列 NaN 行削除
    df = df.dropna(how="all")

    # record_date 正規化
    if "record_date" in df.columns:
        df["record_date"] = df["record_date"].apply(normalize_date)
        df = df.dropna(subset=["record_date"])

    # 数値変換
    for col in ("budget_amount", "actual_amount"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            median_val = df[col].median()
            fill_val = median_val if pd.notna(median_val) else 500000
            df[col] = df[col].fillna(fill_val).clip(lower=0)
        else:
            df[col] = 500000.0

    # is_over_budget 再計算（データ整合性確保）
    df["is_over_budget"] = (df["actual_amount"] > df["budget_amount"]).astype(int)

    # 派生列
    df["variance"] = df["actual_amount"] - df["budget_amount"]
    df["variance_rate"] = df["variance"] / df["budget_amount"].replace(0, float("nan"))
    df["variance_rate"] = df["variance_rate"].fillna(0.0).round(4)
    df["variance"] = df["variance"].round(0)

    df["budget_status"] = df["is_over_budget"].apply(
        lambda x: "超過" if x == 1 else "予算内"
    )

    def calc_grade(rate: float) -> str:
        if rate > 0.1:
            return "大超過"
        elif rate > 0:
            return "小超過"
        else:
            return "予算内"

    df["variance_grade"] = df["variance_rate"].apply(calc_grade)

    # CANONICAL_COLSのみ出力
    available = [c for c in CANONICAL_COLS if c in df.columns]
    df = df[available]

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

    out_path = OUTPUT_DIR / "cleaned_costs_202401.csv"
    result.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\nクレンジング完了: {len(result)} 行")
    print(f"出力: {out_path}")
    print(f"列: {list(result.columns)}")


if __name__ == "__main__":
    main()

"""
C-23: クレンジングスクリプト
data/ 以下の3スタイルCSVを統一フォーマットに変換し output/cleaned_maintenance_202401.csv へ出力
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    "物件ID": "property_id", "property_id": "property_id", "管理番号": "property_id",
    "物件名": "property_name", "property_name": "property_name", "建物名": "property_name",
    "エリア": "area", "area": "area", "地区": "area",
    "物件種別": "property_type", "property_type": "property_type", "種別": "property_type",
    "費用区分": "cost_category", "cost_category": "cost_category", "費目": "cost_category",
    "発生日": "occurrence_date", "occurrence_date": "occurrence_date", "計上日": "occurrence_date",
    "費用金額": "cost_amount", "cost_amount": "cost_amount", "金額": "cost_amount",
    "業者名": "vendor_name", "vendor_name": "vendor_name", "業者": "vendor_name",
    "緊急区分": "is_urgent", "is_urgent": "is_urgent", "緊急対応": "is_urgent",
}

REQUIRED_COLS = [
    "property_id", "property_name", "area", "property_type",
    "cost_category", "occurrence_date", "cost_amount", "vendor_name", "is_urgent",
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
    """is_urgent を bool に統一"""
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    s = str(val).strip().lower()
    return s in ("true", "1", "yes", "緊急あり", "緊急")


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

    # occurrence_date 正規化
    if "occurrence_date" in df.columns:
        df["occurrence_date"] = df["occurrence_date"].apply(normalize_date)
        df = df.dropna(subset=["occurrence_date"])

    # cost_amount: 欠損を中央値で補完
    if "cost_amount" in df.columns:
        df["cost_amount"] = pd.to_numeric(df["cost_amount"], errors="coerce")
        median_amount = df["cost_amount"].median()
        df["cost_amount"] = df["cost_amount"].fillna(median_amount if pd.notna(median_amount) else 100000)
        df["cost_amount"] = df["cost_amount"].clip(lower=0)
    else:
        df["cost_amount"] = 100000.0

    # is_urgent を bool に統一
    if "is_urgent" in df.columns:
        df["is_urgent"] = df["is_urgent"].apply(normalize_bool)
    else:
        df["is_urgent"] = False

    # 計算列
    df["cost_per_unit_flag"] = df["cost_amount"].apply(
        lambda x: "高額" if x > 500000 else ("中額" if x > 100000 else "少額")
    )
    df["is_repair"] = df["cost_category"].isin(["定期修繕", "緊急修繕"])

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
        "property_id", "property_name", "area", "property_type",
        "cost_category", "occurrence_date", "cost_amount", "vendor_name",
        "is_urgent", "cost_per_unit_flag", "is_repair", "source_file",
    ]
    result = result[[c for c in col_order if c in result.columns]]

    out_path = OUTPUT_DIR / "cleaned_maintenance_202401.csv"
    result.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\nクレンジング完了: {len(result)} 行")
    print(f"出力: {out_path}")
    print(f"列: {list(result.columns)}")


if __name__ == "__main__":
    main()

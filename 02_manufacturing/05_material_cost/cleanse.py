import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent
DATA_DIR = BASE / "data"
OUTPUT_DIR = BASE / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    # スタイルA (標準日本語)
    "仕入日":      "purchase_date",
    "原材料コード": "material_code",
    "原材料名":    "material_name",
    "カテゴリ":    "category",
    "仕入先":      "supplier",
    "数量":        "quantity",
    "単価":        "unit_price",
    "前月単価":    "prev_month_price",
    # スタイルB (英語)
    "PurchaseDate":   "purchase_date",
    "MaterialCode":   "material_code",
    "MaterialName":   "material_name",
    "Category":       "category",
    "Supplier":       "supplier",
    "Quantity":       "quantity",
    "UnitPrice":      "unit_price",
    "PrevMonthPrice": "prev_month_price",
    # スタイルC (バリアント日本語)
    "購入日":    "purchase_date",
    "品目コード": "material_code",
    "品目名":    "material_name",
    "品種":      "category",
    "取引先":    "supplier",
    "購入数量":  "quantity",
    "仕入単価":  "unit_price",
    "先月単価":  "prev_month_price",
}

REQUIRED_COLS = [
    "purchase_date", "material_code", "material_name", "category",
    "supplier", "quantity", "unit_price", "prev_month_price",
]


def normalize_date(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s in ("", "NULL", "N/A"):
        return None
    for fmt in ["%Y/%m/%d", "%Y-%m-%d", "%Y年%m月%d日"]:
        try:
            return pd.to_datetime(s, format=fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    try:
        return pd.to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        return None


def normalize_numeric(val):
    if pd.isna(val):
        return None
    s = str(val).strip().replace(",", "").replace("，", "")
    s = s.translate(str.maketrans("０１２３４５６７８９．", "0123456789."))
    try:
        return float(s)
    except ValueError:
        return None


def read_csv_auto(path: Path) -> pd.DataFrame:
    raw = path.read_bytes()
    for enc in ["utf-8-sig", "utf-8", "cp932"]:
        try:
            raw.decode(enc)
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path, encoding="utf-8", errors="replace")


all_frames = []
csv_files = sorted(DATA_DIR.glob("*.csv"))

for f in csv_files:
    try:
        df = read_csv_auto(f)
    except Exception as e:
        print(f"Read error {f.name}: {e}")
        continue

    # 列名正規化
    renamed = {}
    for col in df.columns:
        col_s = str(col).strip()
        if col_s in COLUMN_MAP:
            renamed[col] = COLUMN_MAP[col_s]
        elif str(col).startswith("Unnamed"):
            renamed[col] = f"_drop_{col}"
    df = df.rename(columns=renamed)
    drop_cols = [c for c in df.columns if str(c).startswith("_drop_")]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    df = df.dropna(how="all")

    # 日付正規化
    if "purchase_date" in df.columns:
        df["purchase_date"] = df["purchase_date"].apply(normalize_date)
        df = df.dropna(subset=["purchase_date"])

    # 数値正規化
    for col in ["quantity", "unit_price", "prev_month_price"]:
        if col in df.columns:
            df[col] = df[col].apply(normalize_numeric)
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val if pd.notna(median_val) else 0)
            df[col] = df[col].clip(lower=0)
        else:
            df[col] = 0.0

    # 計算列追加
    prev = df["prev_month_price"].replace(0, float("nan"))
    df["price_change_rate"] = ((df["unit_price"] - prev) / prev).round(6)
    df["total_cost"] = (df["quantity"] * df["unit_price"]).round(0)

    def flag(r):
        if pd.isna(r):
            return "安定"
        if r > 0.2:
            return "急騰"
        if r < -0.2:
            return "急落"
        return "安定"

    df["price_change_flag"] = df["price_change_rate"].apply(flag)
    df["source_file"] = f.name

    # 不要列を除去して順序整理
    keep = [c for c in [
        "purchase_date", "material_code", "material_name", "category",
        "supplier", "quantity", "unit_price", "prev_month_price",
        "price_change_rate", "total_cost", "price_change_flag", "source_file",
    ] if c in df.columns]
    df = df[keep]
    all_frames.append(df)
    print(f"Processed {f.name}: {len(df)} rows")

if all_frames:
    result = pd.concat(all_frames, ignore_index=True)
    result = result.drop_duplicates()
    out_path = OUTPUT_DIR / "cleaned_material_202401.csv"
    result.to_csv(out_path, index=False, encoding="utf-8-sig")
    n_soar = (result["price_change_flag"] == "急騰").sum()
    n_drop = (result["price_change_flag"] == "急落").sum()
    print(f"Complete: {len(result)} rows, 急騰={n_soar}, 急落={n_drop}")
    print(f"Columns: {list(result.columns)}")
else:
    print("No files found in data/")

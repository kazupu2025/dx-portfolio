import pandas as pd
import re
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    "日付": "date", "Date": "date",
    "店舗": "store", "Store": "store", "拠点": "store",
    "食材コード": "ingredient_code", "IngredientCode": "ingredient_code", "品番": "ingredient_code",
    "食材名": "ingredient_name", "IngredientName": "ingredient_name", "品目": "ingredient_name",
    "カテゴリ": "category", "Category": "category", "分類": "category",
    "仕入量(kg)": "purchase_qty", "PurchaseQty": "purchase_qty", "発注量": "purchase_qty",
    "仕入単価(円)": "unit_cost", "UnitCost": "unit_cost", "原価": "unit_cost",
    "使用量(kg)": "used_qty", "UsedQty": "used_qty", "使用数": "used_qty",
    "廃棄量(kg)": "waste_qty", "WasteQty": "waste_qty", "ロス数": "waste_qty",
}

KEEP_COLS = {
    "date", "store", "ingredient_code", "ingredient_name", "category",
    "purchase_qty", "unit_cost", "used_qty", "waste_qty",
    "purchase_cost", "waste_cost", "waste_rate",
    "qty_imputed", "source_file",
}

log_lines = ["# クレンジングログ\n"]


def extract_store(filename: str) -> str:
    m = re.search(r'[ぁ-鿿々ー]+店', filename)
    if m:
        return m.group(0)
    parts = re.split(r'[_\-\s]', Path(filename).stem)
    for part in parts:
        if re.search(r'[ぁ-鿿々ー]{2,}', part):
            return part
    return Path(filename).stem


def read_file(f: Path) -> pd.DataFrame:
    raw_bytes = f.read_bytes()
    enc = "utf-8-sig"
    for candidate in ["utf-8-sig", "utf-8", "cp932"]:
        try:
            raw_bytes.decode(candidate)
            enc = candidate
            break
        except Exception:
            continue
    return pd.read_csv(f, encoding=enc)


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


all_frames = []
files = sorted(Path(".").glob("*.csv"))

for f in files:
    if "output" in str(f).lower():
        continue
    store = extract_store(f.name)
    log_lines.append(f"\n## {f.name} → 店舗: {store}")

    try:
        df = read_file(f)
    except Exception as e:
        log_lines.append(f"- 読み込みエラー: {e}")
        continue

    renamed = {}
    for col in df.columns:
        col_str = str(col).strip()
        if col_str in COLUMN_MAP:
            renamed[col] = COLUMN_MAP[col_str]
        elif str(col).startswith("Unnamed"):
            renamed[col] = f"_drop_{col}"
    df = df.rename(columns=renamed)
    drop_cols = [c for c in df.columns if str(c).startswith("_drop_")]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    df = df.dropna(how="all")

    if "date" in df.columns:
        df["date"] = df["date"].apply(normalize_date)
        df = df.dropna(subset=["date"])

    df["qty_imputed"] = False
    for col in ["purchase_qty", "unit_cost", "used_qty", "waste_qty"]:
        if col in df.columns:
            df[col] = df[col].apply(normalize_numeric)
            if df[col].isna().any():
                df.loc[df[col].isna(), "qty_imputed"] = True
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val if median_val is not None else 0)
            df[col] = df[col].clip(lower=0)
        else:
            df[col] = 0.0

    # 派生列: 仕入コスト、廃棄コスト、ロス率
    df["purchase_cost"] = (df["purchase_qty"] * df["unit_cost"]).round(0)
    df["waste_cost"]    = (df["waste_qty"]    * df["unit_cost"]).round(0)
    df["waste_rate"]    = (df["waste_qty"] / df["purchase_qty"].replace(0, float("nan"))).round(4)
    df["waste_rate"]    = df["waste_rate"].fillna(0)

    df["store"]       = store
    df["source_file"] = f.name

    keep = [c for c in KEEP_COLS if c in df.columns]
    df = df[keep]
    all_frames.append(df)
    log_lines.append(f"- 完了: {len(df)} 行, 廃棄コスト合計: {df['waste_cost'].sum():,.0f}円")

if all_frames:
    result = pd.concat(all_frames, ignore_index=True)
    result = result.drop_duplicates()

    col_order = [
        "date", "store", "ingredient_code", "ingredient_name", "category",
        "purchase_qty", "unit_cost", "used_qty", "waste_qty",
        "purchase_cost", "waste_cost", "waste_rate",
        "qty_imputed", "source_file",
    ]
    result = result[[c for c in col_order if c in result.columns]]
    result.to_csv(OUTPUT_DIR / "cleaned_cost_202401.csv", index=False, encoding="utf-8-sig")
    (OUTPUT_DIR / "cleansing_log.md").write_text("\n".join(log_lines), encoding="utf-8")
    avg_waste = result["waste_rate"].mean() * 100
    print(f"完了: {len(result)} 行, 平均ロス率: {avg_waste:.2f}%")
    print("列:", list(result.columns))
else:
    print("処理対象ファイルが見つかりませんでした")

"""
飲食店売上データクレンジングスクリプト
5店舗分のバラバラな CSV を統一フォーマットに整形する（廃棄列対応）
"""
import pandas as pd
import re
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    "売上額": "sales_amount", "売上金額": "sales_amount",
    "Sales": "sales_amount", "売上": "sales_amount",
    "売上合計": "sales_amount", "販売合計": "sales_amount",
    "売上日": "date", "日付": "date", "日付け": "date",
    "Date": "date", "販売日": "date",
    "商品名": "item_name", "品名": "item_name", "Item": "item_name",
    "Product": "item_name", "商品": "item_name",
    "数量": "quantity", "個数": "quantity", "Qty": "quantity", "数": "quantity",
    "単価": "unit_price", "Price": "unit_price", "価格": "unit_price",
    "カテゴリ": "category", "Category": "category",
    "分類": "category", "商品カテゴリ": "category",
    "店舗": "store_col", "店舗名": "store_col", "Store": "store_col",
    "廃棄数量": "waste_qty", "廃棄": "waste_qty", "WasteQty": "waste_qty",
    "廃棄量": "waste_qty",
    "廃棄金額": "waste_amount", "WasteAmount": "waste_amount",
    "廃棄額": "waste_amount",
}

KEEP_COLS = {"date", "store_name", "item_name", "category",
             "quantity", "unit_price", "sales_amount",
             "waste_qty", "waste_amount",
             "sales_imputed", "source_file"}

STORE_NAME_MAP = {}

log_lines = ["# クレンジングログ\n"]


def extract_store_name(filename: str) -> str:
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
    first_line = raw_bytes.decode(enc, errors="replace").split("\n")[0]
    sep = ";" if first_line.count(";") > first_line.count(",") else ","
    return pd.read_csv(f, encoding=enc, sep=sep)


def normalize_numeric(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s in ("-", "--", "NULL", "N/A", "NA", "none", ""):
        return None
    s = (s.replace(",", "").replace("，", "")
          .replace("¥", "").replace("円", "").strip())
    s = s.translate(str.maketrans("０１２３４５６７８９．", "0123456789."))
    try:
        return float(s)
    except ValueError:
        return None


def normalize_date(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s in ("", "NULL", "N/A"):
        return None
    for fmt in ["%Y/%m/%d", "%Y-%m-%d", "%Y年%m月%d日", "%m/%d/%Y", "%d/%m/%Y"]:
        try:
            return pd.to_datetime(s, format=fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    try:
        return pd.to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        return None


all_frames = []
files = sorted(Path(".").glob("*.csv"))

for f in files:
    if "output" in str(f).lower():
        continue
    store = STORE_NAME_MAP.get(extract_store_name(f.name), extract_store_name(f.name))
    log_lines.append(f"\n## {f.name} → 店舗名: {store}")

    try:
        df = read_file(f)
    except Exception as e:
        log_lines.append(f"- 読み込みエラー: {e}")
        continue

    renamed = {}
    unmapped = []
    for col in df.columns:
        col_str = str(col).strip()
        if col_str in COLUMN_MAP:
            renamed[col] = COLUMN_MAP[col_str]
        elif str(col).startswith("Unnamed"):
            renamed[col] = f"_drop_{col}"
        elif col_str not in KEEP_COLS:
            unmapped.append(col_str)
    df = df.rename(columns=renamed)
    if unmapped:
        log_lines.append(f"- 未マッピング列: {unmapped}")

    drop_cols = [c for c in df.columns if str(c).startswith("_drop_")]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    before = len(df)
    df = df.dropna(how="all")
    if before - len(df):
        log_lines.append(f"- 空白行 {before - len(df)} 行を削除")

    if "date" in df.columns:
        df["date"] = df["date"].apply(normalize_date)
        df = df.dropna(subset=["date"])
    else:
        log_lines.append("- WARNING: date 列が見つからない")

    for col in ["sales_amount", "quantity", "unit_price", "waste_qty", "waste_amount"]:
        if col in df.columns:
            df[col] = df[col].apply(normalize_numeric)
            if col == "sales_amount":
                df["sales_imputed"] = df[col].isna()
                df[col] = df[col].fillna(0)
            elif col in ["waste_qty", "waste_amount"]:
                df[col] = df[col].fillna(0)

    df["store_name"] = store
    df["source_file"] = f.name

    keep = [c for c in KEEP_COLS if c in df.columns]
    df = df[keep]

    all_frames.append(df)
    log_lines.append(f"- 完了: {len(df)} 行")

if all_frames:
    result = pd.concat(all_frames, ignore_index=True)
    result["sales_amount"] = result["sales_amount"].fillna(0)
    if "waste_qty" not in result.columns:
        result["waste_qty"] = 0
    if "waste_amount" not in result.columns:
        result["waste_amount"] = 0
    result["waste_qty"] = result["waste_qty"].fillna(0)
    result["waste_amount"] = result["waste_amount"].fillna(0)
    if "sales_imputed" in result.columns:
        result["sales_imputed"] = result["sales_imputed"].fillna(False).astype(bool)

    before_dedup = len(result)
    result = result.drop_duplicates()
    if before_dedup - len(result):
        log_lines.append(f"- 重複行 {before_dedup - len(result)} 件を除去")

    col_order = ["date", "store_name", "item_name", "category",
                 "quantity", "unit_price", "sales_amount",
                 "waste_qty", "waste_amount",
                 "sales_imputed", "source_file"]
    result = result[[c for c in col_order if c in result.columns]]

    result.to_csv(OUTPUT_DIR / "cleaned_sales_202401.csv", index=False, encoding="utf-8-sig")

    log_lines.append(f"\n## 完了サマリー")
    log_lines.append(f"- 総行数: {len(result)}")
    log_lines.append(f"- 店舗数: {result['store_name'].nunique()}")
    log_lines.append(f"- 店舗一覧: {sorted(result['store_name'].unique().tolist())}")

    (OUTPUT_DIR / "cleansing_log.md").write_text("\n".join(log_lines), encoding="utf-8")
    print(f"完了: {len(result)} 行, {result['store_name'].nunique()} 店舗")
    print("列:", list(result.columns))
else:
    print("処理対象ファイルが見つかりませんでした")

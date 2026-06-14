import pandas as pd
import re
from pathlib import Path

BASE_DIR = Path("C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/05_logistics/01_inventory")
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    "日付": "date", "Date": "date", "集計日": "date",
    "倉庫名": "warehouse", "Warehouse": "warehouse", "倉庫": "warehouse",
    "品目コード": "item_code", "ItemCode": "item_code", "コード": "item_code",
    "品目名": "item_name", "ItemName": "item_name", "品名": "item_name",
    "カテゴリ": "category", "Category": "category", "分類": "category",
    "在庫数量": "stock_qty", "StockQty": "stock_qty", "在庫": "stock_qty",
    "最低在庫数": "min_stock_qty", "MinStock": "min_stock_qty", "安全在庫": "min_stock_qty",
    "単価": "unit_cost", "UnitCost": "unit_cost", "原価": "unit_cost",
    "入庫数量": "received_qty", "ReceivedQty": "received_qty", "入庫": "received_qty",
    "出庫数量": "shipped_qty", "ShippedQty": "shipped_qty", "出庫": "shipped_qty",
}

KEEP_COLS = {
    "date", "warehouse", "item_code", "item_name", "category",
    "stock_qty", "min_stock_qty", "unit_cost", "received_qty", "shipped_qty",
    "stock_imputed", "source_file",
}

log_lines = ["# クレンジングログ\n"]


def extract_warehouse_name(filename: str) -> str:
    m = re.search(r'[ぁ-鿿々ー]+(?:倉庫|センター|デポ)', filename)
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
files = sorted(BASE_DIR.glob("*.csv"))

for f in files:
    warehouse = extract_warehouse_name(f.name)
    log_lines.append(f"\n## {f.name} → 倉庫名: {warehouse}")

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

    for col in ["stock_qty", "min_stock_qty", "unit_cost", "received_qty", "shipped_qty"]:
        if col in df.columns:
            df[col] = df[col].apply(normalize_numeric)
            if col == "stock_qty":
                df["stock_imputed"] = df[col].isna()
                df[col] = df[col].fillna(0)
            else:
                df[col] = df[col].fillna(0)

    df["warehouse"] = warehouse
    df["source_file"] = f.name

    keep = [c for c in KEEP_COLS if c in df.columns]
    df = df[keep]

    all_frames.append(df)
    log_lines.append(f"- 完了: {len(df)} 行")

if all_frames:
    result = pd.concat(all_frames, ignore_index=True)

    for col in ["stock_qty", "min_stock_qty", "unit_cost", "received_qty", "shipped_qty"]:
        if col not in result.columns:
            result[col] = 0
        result[col] = result[col].fillna(0)

    if "stock_imputed" in result.columns:
        result["stock_imputed"] = result["stock_imputed"].fillna(False).astype(bool)
    else:
        result["stock_imputed"] = False

    before_dedup = len(result)
    result = result.drop_duplicates()
    if before_dedup - len(result):
        log_lines.append(f"- 重複行 {before_dedup - len(result)} 件を除去")

    col_order = [
        "date", "warehouse", "item_code", "item_name", "category",
        "stock_qty", "min_stock_qty", "unit_cost", "received_qty", "shipped_qty",
        "stock_imputed", "source_file",
    ]
    result = result[[c for c in col_order if c in result.columns]]

    result.to_csv(OUTPUT_DIR / "cleaned_inventory_202401.csv", index=False, encoding="utf-8-sig")

    log_lines.append(f"\n## 完了サマリー")
    log_lines.append(f"- 総行数: {len(result)}")
    log_lines.append(f"- 倉庫数: {result['warehouse'].nunique()}")
    log_lines.append(f"- 倉庫一覧: {sorted(result['warehouse'].unique().tolist())}")

    (OUTPUT_DIR / "cleansing_log.md").write_text("\n".join(log_lines), encoding="utf-8")
    print(f"完了: {len(result)} 行, {result['warehouse'].nunique()} 倉庫")
    print("列:", list(result.columns))
else:
    print("処理対象ファイルが見つかりませんでした")

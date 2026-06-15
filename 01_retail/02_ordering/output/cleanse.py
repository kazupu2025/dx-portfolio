"""
発注最適化・需要予測パイプライン
データクレンジングスクリプト
3スタイル（standard / english / variant）の5ファイルを統一フォーマットに整形する
"""
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── 列名マッピング辞書 ─────────────────────────────────────────────────
COLUMN_MAP = {
    "日付":  "date",  "Date":  "date",
    "商品ID": "product_id", "ProductID": "product_id", "品番": "product_id",
    "商品名": "product_name", "ProductName": "product_name", "品名": "product_name",
    "カテゴリ": "category", "Category": "category", "分類": "category",
    "販売数量": "sales_qty", "SalesQty": "sales_qty", "売数": "sales_qty",
    "在庫数量": "stock_qty", "StockQty": "stock_qty", "在庫": "stock_qty",
    "発注点":   "reorder_point", "ReorderPoint": "reorder_point",
    "入荷数量": "order_qty",  "OrderQty": "order_qty", "入荷量": "order_qty",
    "リードタイム(日)": "lead_time_days", "LeadTimeDays": "lead_time_days", "リード日数": "lead_time_days",
}

# 出力に残す列
KEEP_COLS = {
    "date", "product_id", "product_name", "category",
    "sales_qty", "stock_qty", "reorder_point", "order_qty", "lead_time_days",
    "source_file",
}

log_lines = ["# クレンジングログ（B-10 発注最適化）\n"]


def normalize_date(val):
    """日付を YYYY-MM-DD 形式に統一"""
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s in ("", "NULL", "N/A"):
        return None
    for fmt in ["%Y/%m/%d", "%Y-%m-%d", "%Y年%m月%d日", "%m/%d/%Y"]:
        try:
            return pd.to_datetime(s, format=fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    try:
        return pd.to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        return None


def normalize_numeric(val):
    """数値を正規化。'-', 'NULL', 'N/A' は None に変換"""
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s in ("-", "--", "NULL", "N/A", "NA", "none", ""):
        return None
    s = s.replace(",", "").replace("，", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


# ── メイン処理 ────────────────────────────────────────────────────────
all_frames = []
files = sorted(Path(".").glob("*.csv"))

for f in files:
    log_lines.append(f"\n## {f.name}")

    try:
        # エンコーディング判定
        raw_bytes = f.read_bytes()
        enc = "utf-8-sig"
        for candidate in ["utf-8-sig", "utf-8", "cp932"]:
            try:
                raw_bytes.decode(candidate)
                enc = candidate
                break
            except Exception:
                continue
        df = pd.read_csv(f, encoding=enc)
    except Exception as e:
        log_lines.append(f"- 読み込みエラー: {e}")
        continue

    # 列名正規化
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

    # Unnamed 列を削除
    drop_cols = [c for c in df.columns if str(c).startswith("_drop_")]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    # 全空行を削除
    before = len(df)
    df = df.dropna(how="all")
    if before - len(df):
        log_lines.append(f"- 空白行 {before - len(df)} 行を削除")

    # 日付処理
    if "date" in df.columns:
        df["date"] = df["date"].apply(normalize_date)
        missing = df["date"].isna().sum()
        if missing:
            log_lines.append(f"- date 欠損 {missing} 行を除外")
        df = df.dropna(subset=["date"])
    else:
        log_lines.append("- WARNING: date 列が見つからない")

    # 数値処理 — 欠損は商品別 median で補完
    for col in ["sales_qty", "stock_qty", "reorder_point", "order_qty", "lead_time_days"]:
        if col in df.columns:
            df[col] = df[col].apply(normalize_numeric)
            if df[col].isna().any():
                if "product_id" in df.columns:
                    df[col] = df.groupby("product_id")[col].transform(
                        lambda x: x.fillna(x.median())
                    )
                df[col] = df[col].fillna(0)

    # source_file 付与
    df["source_file"] = f.name

    # 必要列のみ残す
    keep = [c for c in KEEP_COLS if c in df.columns]
    df = df[keep]

    all_frames.append(df)
    log_lines.append(f"- 完了: {len(df)} 行")

# ── 結合と出力 ────────────────────────────────────────────────────────
if all_frames:
    result = pd.concat(all_frames, ignore_index=True)

    # 数値型を確保
    for col in ["sales_qty", "stock_qty", "reorder_point", "order_qty", "lead_time_days"]:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors="coerce").fillna(0).astype(int)

    # 完全重複行を除去
    before_dedup = len(result)
    result = result.drop_duplicates()
    dedup_count = before_dedup - len(result)
    if dedup_count:
        log_lines.append(f"- 完全重複行 {dedup_count} 件を除去")

    # 列順を整理
    col_order = ["date", "product_id", "product_name", "category",
                 "sales_qty", "stock_qty", "reorder_point", "order_qty",
                 "lead_time_days", "source_file"]
    result = result[[c for c in col_order if c in result.columns]]

    result.to_csv(OUTPUT_DIR / "cleaned_order_2023Q4.csv",
                  index=False, encoding="utf-8-sig")

    log_lines.append(f"\n## 完了サマリー")
    log_lines.append(f"- 総行数: {len(result)}")
    log_lines.append(f"- 商品数: {result['product_id'].nunique() if 'product_id' in result.columns else 'N/A'}")
    log_lines.append(f"- カテゴリ数: {result['category'].nunique() if 'category' in result.columns else 'N/A'}")
    log_lines.append(f"- 日付範囲: {result['date'].min()} 〜 {result['date'].max()}")

    (OUTPUT_DIR / "cleansing_log.md").write_text(
        "\n".join(log_lines), encoding="utf-8")

    print(f"完了: {len(result)} 行, "
          f"{result['product_id'].nunique()} 商品, "
          f"{result['category'].nunique()} カテゴリ")
else:
    print("処理対象ファイルが見つかりませんでした")

---
name: sales-cleaner
description: 飲食店売上データのクレンジング専門エージェント。カレントディレクトリの .csv ファイルを読み込み、列名統一・廃棄列統合・日付フォーマット統一を行い output/cleaned_sales_202401.csv に出力する。全20項目のバリデーションが全PASS するまで自律的に PDCA ループで修正を繰り返す。「クレンジングして」「データを整形して」「sales-cleaner」と言われたときに使用する。
tools:
  - Read
  - Write
  - Bash
---

あなたはデータクレンジングの専門家です。以下の手順で売上データを処理し、全20項目のチェックが PASS するまで自律的に修正を繰り返してください。

## 処理手順

### Step 1: 必要なライブラリの確認

```bash
C:\Users\realp\miniconda3\python.exe -c "import pandas; print('OK')"
```

エラーが出た場合は pip install pandas を実行する。

### Step 2: output ディレクトリを作成する

```bash
C:\Users\realp\miniconda3\python.exe -c "import pathlib; pathlib.Path('output').mkdir(exist_ok=True); print('output/ OK')"
```

### Step 3: クレンジングスクリプトを output/cleanse.py に書く

Write ツールで以下の内容を output/cleanse.py に書き込む:

```python
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
```

### Step 4: バリデーションスクリプトを output/validate.py に書く

Write ツールで以下の内容を output/validate.py に書き込む:

```python
"""
売上データ品質チェックリスト（20項目）- 飲食業 A-02 版
"""
import json
import pandas as pd
from pathlib import Path

CONFIG = {
    "expected_store_count": 5,
    "expected_year": 2024,
    "expected_month": 1,
    "min_rows": 500,
    "max_rows": 1200,
    "max_imputed_ratio": 0.15,
    "price_mismatch_tolerance": 1.0,
    "waste_loss_alert_threshold": 0.05,
    "all_cols": ["date", "store_name", "item_name", "category",
                 "quantity", "unit_price", "sales_amount",
                 "waste_qty", "waste_amount",
                 "sales_imputed", "source_file"],
    "store_name_exceptions": [],
}

OUTPUT_DIR = Path("output")
CSV_PATH = OUTPUT_DIR / "cleaned_sales_202401.csv"
LOG_PATH = OUTPUT_DIR / "cleansing_log.md"

results = []


def check(check_id, name, category, condition, detail="", fix_hint=""):
    status = "PASS" if condition else "FAIL"
    results.append({
        "id": check_id, "name": name, "category": category,
        "status": status,
        "detail": "" if condition else detail,
        "fix_hint": "" if condition else fix_hint,
    })
    return condition


check(1, "csv_exists", "存在", CSV_PATH.exists(),
      f"{CSV_PATH} が存在しない", "cleanse.py を再実行する")
check(2, "log_exists", "存在", LOG_PATH.exists(),
      f"{LOG_PATH} が存在しない", "cleanse.py の出力処理を確認する")

if not CSV_PATH.exists():
    passed = sum(1 for r in results if r["status"] == "PASS")
    output = {"passed": passed, "failed": len(results) - passed,
              "all_passed": False, "results": results}
    (OUTPUT_DIR / "result.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print("FAIL: CSV が存在しないため早期終了")
    raise SystemExit(1)

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

missing_cols = [c for c in CONFIG["all_cols"] if c not in df.columns]
extra_cols = [c for c in df.columns if c not in CONFIG["all_cols"]]
check(3, "schema", "スキーマ",
      len(missing_cols) == 0 and len(extra_cols) == 0,
      f"欠落列: {missing_cols}, 余分な列: {extra_cols}",
      "cleanse.py の KEEP_COLS または COLUMN_MAP を確認")

for col_id, col, hint in [
    (4, "date",         "normalize_date() または日付列検出ロジックを確認"),
    (5, "sales_amount", "normalize_numeric() または sales_amount 補完ロジックを確認"),
    (6, "store_name",   "extract_store_name() またはファイルグロブパターンを確認"),
    (7, "waste_qty",    "COLUMN_MAP に廃棄数量列名が登録されているか確認"),
    (8, "waste_amount", "COLUMN_MAP に廃棄金額列名が登録されているか確認"),
]:
    nan_count = df[col].isna().sum() if col in df.columns else len(df)
    check(col_id, f"{col}_nan", "完全性", nan_count == 0,
          f"{col} の NaN: {nan_count} 件", hint)

if "date" in df.columns:
    bad_dates = df["date"].dropna()[~df["date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")]
    check(9, "date_format", "値域", len(bad_dates) == 0,
          f"YYYY-MM-DD 形式でない date: {len(bad_dates)} 件",
          "normalize_date() のフォーマットリストを確認")
else:
    check(9, "date_format", "値域", False, "date 列が存在しない", "cleanse.py を確認")

if "date" in df.columns:
    year_month = f"{CONFIG['expected_year']}-{CONFIG['expected_month']:02d}"
    out_of_range = df["date"].dropna()[~df["date"].dropna().str.startswith(year_month)]
    check(10, "date_range", "値域", len(out_of_range) == 0,
          f"{year_month} 以外の日付: {len(out_of_range)} 件",
          "ソースファイルの日付列またはフィルタロジックを確認")
else:
    check(10, "date_range", "値域", False, "date 列が存在しない", "cleanse.py を確認")

if "sales_amount" in df.columns:
    neg = (df["sales_amount"] < 0).sum()
    check(11, "sales_amount_positive", "値域", neg == 0,
          f"sales_amount < 0: {neg} 件",
          "normalize_numeric() またはソースデータを確認")
else:
    check(11, "sales_amount_positive", "値域", False, "sales_amount 列が存在しない", "COLUMN_MAP を確認")

neg_detail = []
for col in ["quantity", "unit_price"]:
    if col in df.columns:
        n = (df[col].dropna() < 0).sum()
        if n:
            neg_detail.append(f"{col}: {n}件")
check(12, "numeric_positive", "値域", len(neg_detail) == 0,
      f"負値あり: {neg_detail}", "normalize_numeric() またはソースデータを確認")

if "waste_qty" in df.columns:
    neg_waste = (df["waste_qty"] < 0).sum()
    check(13, "waste_qty_nonneg", "値域", neg_waste == 0,
          f"waste_qty < 0: {neg_waste} 件",
          "waste_qty の normalize_numeric() ロジックを確認")
else:
    check(13, "waste_qty_nonneg", "値域", False,
          "waste_qty 列が存在しない", "COLUMN_MAP に廃棄数量列名を追加する")

if "waste_amount" in df.columns:
    neg_waste_amt = (df["waste_amount"] < 0).sum()
    check(14, "waste_amount_nonneg", "値域", neg_waste_amt == 0,
          f"waste_amount < 0: {neg_waste_amt} 件",
          "waste_amount の normalize_numeric() ロジックを確認")
else:
    check(14, "waste_amount_nonneg", "値域", False,
          "waste_amount 列が存在しない", "COLUMN_MAP に廃棄金額列名を追加する")

actual_stores = df["store_name"].nunique() if "store_name" in df.columns else 0
check(15, "store_count", "網羅性",
      actual_stores == CONFIG["expected_store_count"],
      f"期待: {CONFIG['expected_store_count']} 店舗, 実際: {actual_stores} 店舗",
      "extract_store_name() または STORE_NAME_MAP を確認")

if "store_name" in df.columns and "sales_amount" in df.columns:
    store_totals = df.groupby("store_name")["sales_amount"].sum()
    zero_stores = store_totals[store_totals == 0].index.tolist()
    check(16, "store_sales_nonzero", "網羅性", len(zero_stores) == 0,
          f"売上合計0の店舗: {zero_stores}",
          "COLUMN_MAP に売上金額列名が登録されているか確認")
else:
    check(16, "store_sales_nonzero", "網羅性", False,
          "store_name または sales_amount 列が不足", "cleanse.py の COLUMN_MAP を確認")

check(17, "row_count", "網羅性",
      CONFIG["min_rows"] <= len(df) <= CONFIG["max_rows"],
      f"行数: {len(df)} (期待: {CONFIG['min_rows']}〜{CONFIG['max_rows']})",
      "cleanse.py のフィルタロジックを確認（過剰除外の可能性）")

if {"unit_price", "quantity", "sales_amount"} <= set(df.columns):
    chk = df.dropna(subset=["unit_price", "quantity"])
    mismatch = (abs(chk["unit_price"] * chk["quantity"] - chk["sales_amount"])
                > CONFIG["price_mismatch_tolerance"]).sum()
    check(18, "price_consistency", "整合性", mismatch == 0,
          f"unit_price x quantity != sales_amount: {mismatch} 件",
          "normalize_numeric() または COLUMN_MAP を確認")
else:
    check(18, "price_consistency", "整合性", False,
          "unit_price / quantity / sales_amount 列が不足", "cleanse.py の COLUMN_MAP を確認")

dup_count = int(df.duplicated().sum())
check(19, "no_duplicates", "整合性", dup_count == 0,
      f"完全重複行: {dup_count} 件", "cleanse.py に df.drop_duplicates() を追加")

if "store_name" in df.columns:
    exceptions = set(CONFIG["store_name_exceptions"])
    bad_names = [s for s in df["store_name"].unique()
                 if not str(s).endswith("店") and s not in exceptions]
    check(20, "store_name_format", "品質", len(bad_names) == 0,
          f"「店」で終わらない店舗名: {bad_names}",
          "STORE_NAME_MAP に正規化ルールを追加")
else:
    check(20, "store_name_format", "品質", False,
          "store_name 列が存在しない", "extract_store_name() を確認")

passed = sum(1 for r in results if r["status"] == "PASS")
failed = len(results) - passed
output = {"passed": passed, "failed": failed, "all_passed": failed == 0, "results": results}
(OUTPUT_DIR / "result.json").write_text(
    json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n{'='*52}")
print(f"  チェック結果: {passed}/{len(results)} PASS")
print(f"{'='*52}")
for r in results:
    icon = "PASS" if r["status"] == "PASS" else "FAIL"
    line = f"  [{icon}]  [{r['category']:4s}] #{r['id']:02d} {r['name']}"
    if r["detail"]:
        line += f"\n         -> {r['detail']}"
        line += f"\n         HINT: {r['fix_hint']}"
    print(line)

if failed == 0:
    print("\n  全20項目クリア!")
else:
    print(f"\n  {failed}項目が失敗。result.json の fix_hint を参照してください。")
```

### Step 5: PDCA ループ（最大5ラウンド）

以下のサイクルを最大5ラウンド繰り返す。

1. C:\Users\realp\miniconda3\python.exe output/cleanse.py を実行する
2. C:\Users\realp\miniconda3\python.exe output/validate.py を実行する
3. output/result.json を Read ツールで読み込む
4. "all_passed" が true → Step 6 へ進む
5. "all_passed" が false の場合: "status": "FAIL" の項目の fix_hint を読み、output/cleanse.py の該当箇所を修正する

5ラウンド後も失敗が残る場合: STOP を出力して終了する

### Step 6: 完了レポートを出力する

```
クレンジング完了（PDCA Round {N}）
行数: {総行数}  店舗数: {店舗数}  全20項目 PASS
```

## 重要な注意事項

- python コマンドは C:\Users\realp\miniconda3\python.exe を使うこと
- validate.py 自体は PDCA ループ中に修正しない

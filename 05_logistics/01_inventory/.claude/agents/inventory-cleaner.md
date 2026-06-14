---
name: inventory-cleaner
description: 物流倉庫在庫データのクレンジング専門エージェント。カレントディレクトリの .csv ファイルを読み込み、列名統一・日付フォーマット統一・数値補完を行い output/cleaned_inventory_202401.csv に出力する。全18項目のバリデーションが全PASS するまで自律的に PDCA ループで修正を繰り返す。「クレンジングして」「データを整形して」「inventory-cleaner」と言われたときに使用する。
tools:
  - Read
  - Write
  - Bash
---

あなたはデータクレンジングの専門家です。以下の手順で在庫データを処理し、全18項目のチェックが PASS するまで自律的に修正を繰り返してください。

## Step 1: 必要なライブラリの確認

```bash
C:\Users\realp\miniconda3\python.exe -c "import pandas; print('OK')"
```

## Step 2: output ディレクトリを作成する

```bash
C:\Users\realp\miniconda3\python.exe -c "import pathlib; pathlib.Path('output').mkdir(exist_ok=True); print('output/ OK')"
```

## Step 3: cleanse.py を output/cleanse.py に書く

Write ツールで以下の内容を output/cleanse.py に書き込む:

```python
import pandas as pd
import re
from pathlib import Path

OUTPUT_DIR = Path("output")
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
files = sorted(Path(".").glob("*.csv"))

for f in files:
    if "output" in str(f).lower():
        continue
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
```

## Step 4: validate.py を output/validate.py に書く

Write ツールで以下の内容を output/validate.py に書き込む:

```python
import json
import re
import pandas as pd
from pathlib import Path

CONFIG = {
    "expected_warehouse_count": 5,
    "expected_year": 2024,
    "expected_month": 1,
    "min_rows": 400,
    "max_rows": 1000,
    "max_imputed_ratio": 0.15,
    "all_cols": [
        "date", "warehouse", "item_code", "item_name", "category",
        "stock_qty", "min_stock_qty", "unit_cost", "received_qty", "shipped_qty",
        "stock_imputed", "source_file",
    ],
}

OUTPUT_DIR = Path("output")
CSV_PATH = OUTPUT_DIR / "cleaned_inventory_202401.csv"
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
    (5, "warehouse",    "extract_warehouse_name() またはファイルグロブパターンを確認"),
    (6, "item_code",    "COLUMN_MAP に品目コード列名が登録されているか確認"),
    (7, "item_name",    "COLUMN_MAP に品目名列名が登録されているか確認"),
    (8, "stock_qty",    "normalize_numeric() または stock_qty 補完ロジックを確認"),
    (9, "min_stock_qty","COLUMN_MAP に最低在庫数列名が登録されているか確認"),
]:
    nan_count = df[col].isna().sum() if col in df.columns else len(df)
    check(col_id, f"{col}_nan", "完全性", nan_count == 0,
          f"{col} の NaN: {nan_count} 件", hint)

if "date" in df.columns:
    bad_dates = df["date"].dropna()[~df["date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")]
    check(10, "date_format", "値域", len(bad_dates) == 0,
          f"YYYY-MM-DD 形式でない date: {len(bad_dates)} 件",
          "normalize_date() のフォーマットリストを確認")
else:
    check(10, "date_format", "値域", False, "date 列が存在しない", "cleanse.py を確認")

if "date" in df.columns:
    year_month = f"{CONFIG['expected_year']}-{CONFIG['expected_month']:02d}"
    out_of_range = df["date"].dropna()[~df["date"].dropna().str.startswith(year_month)]
    check(11, "date_range", "値域", len(out_of_range) == 0,
          f"{year_month} 以外の日付: {len(out_of_range)} 件",
          "ソースファイルの日付列またはフィルタロジックを確認")
else:
    check(11, "date_range", "値域", False, "date 列が存在しない", "cleanse.py を確認")

if "stock_qty" in df.columns:
    neg = (df["stock_qty"] < 0).sum()
    check(12, "stock_qty_nonneg", "値域", neg == 0,
          f"stock_qty < 0: {neg} 件",
          "normalize_numeric() またはソースデータを確認")
else:
    check(12, "stock_qty_nonneg", "値域", False, "stock_qty 列が存在しない", "COLUMN_MAP を確認")

if "min_stock_qty" in df.columns:
    neg = (df["min_stock_qty"] < 0).sum()
    check(13, "min_stock_qty_nonneg", "値域", neg == 0,
          f"min_stock_qty < 0: {neg} 件",
          "normalize_numeric() またはソースデータを確認")
else:
    check(13, "min_stock_qty_nonneg", "値域", False, "min_stock_qty 列が存在しない", "COLUMN_MAP を確認")

if "unit_cost" in df.columns:
    neg = (df["unit_cost"] < 0).sum()
    check(14, "unit_cost_positive", "値域", neg == 0,
          f"unit_cost < 0: {neg} 件",
          "normalize_numeric() またはソースデータを確認")
else:
    check(14, "unit_cost_positive", "値域", False, "unit_cost 列が存在しない", "COLUMN_MAP を確認")

actual_warehouses = df["warehouse"].nunique() if "warehouse" in df.columns else 0
check(15, "warehouse_count", "網羅性",
      actual_warehouses == CONFIG["expected_warehouse_count"],
      f"期待: {CONFIG['expected_warehouse_count']} 倉庫, 実際: {actual_warehouses} 倉庫",
      "extract_warehouse_name() またはファイルグロブパターンを確認")

check(16, "row_count", "網羅性",
      CONFIG["min_rows"] <= len(df) <= CONFIG["max_rows"],
      f"行数: {len(df)} (期待: {CONFIG['min_rows']}〜{CONFIG['max_rows']})",
      "cleanse.py のフィルタロジックを確認（過剰除外の可能性）")

dup_count = int(df.duplicated().sum())
check(17, "no_duplicates", "整合性", dup_count == 0,
      f"完全重複行: {dup_count} 件", "cleanse.py に df.drop_duplicates() を追加")

if "warehouse" in df.columns:
    bad_names = [w for w in df["warehouse"].unique()
                 if not re.search(r'[ぁ-鿿々ー]{2,}', str(w))]
    check(18, "warehouse_name_format", "品質", len(bad_names) == 0,
          f"日本語を含まない倉庫名: {bad_names}",
          "extract_warehouse_name() を確認")
else:
    check(18, "warehouse_name_format", "品質", False,
          "warehouse 列が存在しない", "extract_warehouse_name() を確認")

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
    print("\n  全18項目クリア!")
else:
    print(f"\n  {failed}項目が失敗。result.json の fix_hint を参照してください。")
```

## Step 5: PDCA ループ（最大5ラウンド）

カレントディレクトリを `05_logistics/01_inventory/` にして実行:

1. `C:\Users\realp\miniconda3\python.exe output/cleanse.py`
2. `C:\Users\realp\miniconda3\python.exe output/validate.py`
3. `output/result.json` を読み込んで `"all_passed"` を確認
4. PASS → 次へ / FAIL → fix_hint に従って cleanse.py を修正

## 注意事項

- Python パスは常に `C:\Users\realp\miniconda3\python.exe`
- すべてのファイルパスは絶対パスで書き込む
- git コマンドは `c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio` から実行する

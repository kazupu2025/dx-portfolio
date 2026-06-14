# A-02 飲食×日次売上・廃棄ロス集計レポート 実装プラン

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A-01（小売売上分析）を飲食業向けに転用し、廃棄ロス率の集計・可視化・Streamlit Web アプリを構築する

**Architecture:** A-01 と同じ Sub-agents Pipeline Pattern（cleaner → analyst → viz-engineer）を踏襲。
新規追加: 廃棄数量(`waste_qty`)・廃棄金額(`waste_amount`)列 + 廃棄ロス率計算 + 廃棄ロス可視化。
転用難易度: ★★★（config と COLUMN_MAP 修正のみで動く）

**Tech Stack:** Python（C:\Users\realp\miniconda3\python.exe）, pandas, openpyxl, streamlit, matplotlib, seaborn, japanize-matplotlib, pyyaml, pytest

---

## ファイル構成

```
06_restaurant/01_daily_sales/
├── .claude/agents/
│   ├── sales-cleaner.md           ← Task 1 で作成（廃棄列対応）
│   ├── data-analyst.md            ← Task 1 で作成（廃棄ロス率分析）
│   └── data-viz-engineer.md       ← Task 5 で作成
├── output/
│   ├── cleanse.py                 ← Task 2: sales-cleaner エージェントが生成
│   ├── validate.py                ← Task 2: sales-cleaner エージェントが生成
│   ├── cleansing_log.md           ← Task 2 実行後
│   ├── cleaned_sales_202401.csv   ← Task 2 実行後
│   ├── result.json                ← Task 2 実行後
│   ├── analyze.py                 ← Task 3: data-analyst エージェントが生成
│   ├── validate_report.py         ← Task 3: data-analyst エージェントが生成
│   ├── analysis_report.md         ← Task 3 実行後
│   ├── result_analysis.json       ← Task 3 実行後
│   ├── visualize.py               ← Task 5: data-viz-engineer が生成
│   └── charts/
│       ├── bar_store_sales.png
│       ├── line_daily_sales.png
│       └── bar_waste_loss.png     ← A-02 追加
├── tests/
│   ├── test_cleaner_output.py     ← Task 6 で作成
│   ├── test_analyst_output.py     ← Task 6 で作成
│   └── test_viz_output.py         ← Task 6 で作成
├── 01_渋谷店_売上_202401.csv      ← Task 1 で生成（標準列名）
├── 02_新宿店_売上_202401.csv      ← Task 1 で生成（英語列名）
├── 03_池袋店_売上_202401.csv      ← Task 1 で生成（バリアント列名）
├── 04_横浜店_売上_202401.csv      ← Task 1 で生成（標準列名）
├── 05_大阪店_売上_202401.csv      ← Task 1 で生成（標準列名）
├── app.py                         ← Task 5 で作成
├── run_pipeline.py                ← Task 1 で作成
├── config.yml                     ← Task 1 で作成
└── requirements.txt               ← Task 1 で作成
```

---

## Task 1: ディレクトリ・設定・エージェント定義・サンプルデータ

**Files:**
- Create: `06_restaurant/01_daily_sales/config.yml`
- Create: `06_restaurant/01_daily_sales/requirements.txt`
- Create: `06_restaurant/01_daily_sales/run_pipeline.py`
- Create: `06_restaurant/01_daily_sales/.claude/agents/sales-cleaner.md`
- Create: `06_restaurant/01_daily_sales/.claude/agents/data-analyst.md`
- Create: `06_restaurant/01_daily_sales/01_渋谷店_売上_202401.csv` ～ `05_大阪店_売上_202401.csv`

- [ ] **Step 1: ディレクトリを作成する**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\06_restaurant\01_daily_sales
mkdir output
mkdir tests
mkdir .claude\agents
```

- [ ] **Step 2: config.yml を作成する**

Write `06_restaurant/01_daily_sales/config.yml`:

```yaml
expected_store_count: 5
expected_year: 2024
expected_month: 1
min_rows: 500
max_rows: 1200
max_imputed_ratio: 0.15
price_mismatch_tolerance: 1.0
waste_loss_alert_threshold: 0.05
store_name_exceptions: []
```

- [ ] **Step 3: requirements.txt を作成する**

Write `06_restaurant/01_daily_sales/requirements.txt`:

```
pandas
openpyxl
matplotlib
seaborn
japanize-matplotlib
streamlit>=1.30.0
pyyaml
pytest
tabulate
```

- [ ] **Step 4: run_pipeline.py を作成する**

Write `06_restaurant/01_daily_sales/run_pipeline.py`:

```python
"""
飲食×廃棄ロス 売上データパイプライン実行スクリプト
使用法: python run_pipeline.py
"""
import subprocess
import sys
from pathlib import Path

PYTHON = r"C:\Users\realp\miniconda3\python.exe"

def run(script: str, label: str):
    print(f"\n{'='*50}")
    print(f"  {label}")
    print(f"{'='*50}")
    result = subprocess.run([PYTHON, script])
    if result.returncode != 0:
        print(f"\nERROR: {label} が失敗しました")
        sys.exit(1)

run("output/cleanse.py",          "Step 1: データクレンジング")
run("output/validate.py",         "Step 2: クレンジング品質チェック（20項目）")
run("output/analyze.py",          "Step 3: 廃棄ロス分析")
run("output/validate_report.py",  "Step 4: レポート品質チェック（7項目）")
run("output/visualize.py",        "Step 5: グラフ生成")
print("\nパイプライン完了! streamlit run app.py で結果を確認してください")
```

- [ ] **Step 5: sales-cleaner エージェント定義を作成する**

Write `06_restaurant/01_daily_sales/.claude/agents/sales-cleaner.md`:

````markdown
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

エラーが出た場合は `pip install pandas` を実行する。

### Step 2: output ディレクトリを作成する

```bash
mkdir -p output
```

### Step 3: クレンジングスクリプトを output/cleanse.py に書く

Write ツールで以下の内容を `output/cleanse.py` に書き込む:

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
    # 売上金額
    "売上額": "sales_amount", "売上金額": "sales_amount",
    "Sales": "sales_amount", "売上": "sales_amount",
    "売上合計": "sales_amount", "販売合計": "sales_amount",
    # 日付
    "売上日": "date", "日付": "date", "日付け": "date",
    "Date": "date", "販売日": "date",
    # 商品名
    "商品名": "item_name", "品名": "item_name", "Item": "item_name",
    "Product": "item_name", "商品": "item_name",
    # 数量
    "数量": "quantity", "個数": "quantity", "Qty": "quantity", "数": "quantity",
    # 単価
    "単価": "unit_price", "Price": "unit_price", "価格": "unit_price",
    # カテゴリ
    "カテゴリ": "category", "Category": "category",
    "分類": "category", "商品カテゴリ": "category",
    # 店舗列
    "店舗": "store_col", "店舗名": "store_col", "Store": "store_col",
    # ── 廃棄列（A-02 追加）──
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
    if str(f).startswith("output"):
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

Write ツールで以下の内容を `output/validate.py` に書き込む:

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

if "date" in df.columns:
    year_month = f"{CONFIG['expected_year']}-{CONFIG['expected_month']:02d}"
    out_of_range = df["date"].dropna()[~df["date"].dropna().str.startswith(year_month)]
    check(10, "date_range", "値域", len(out_of_range) == 0,
          f"{year_month} 以外の日付: {len(out_of_range)} 件",
          "ソースファイルの日付列またはフィルタロジックを確認")

if "sales_amount" in df.columns:
    neg = (df["sales_amount"] < 0).sum()
    check(11, "sales_amount_positive", "値域", neg == 0,
          f"sales_amount < 0: {neg} 件",
          "normalize_numeric() またはソースデータを確認")

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

1. `C:\Users\realp\miniconda3\python.exe output/cleanse.py` を実行する
2. `C:\Users\realp\miniconda3\python.exe output/validate.py` を実行する
3. `output/result.json` を Read ツールで読み込む
4. `"all_passed"` が `true` → Step 6 へ進む
5. `"all_passed"` が `false` の場合:
   - `"status": "FAIL"` の項目の `fix_hint` を読み、`output/cleanse.py` の該当箇所を修正する
   - 修正内容を `output/cleansing_log.md` に追記する
6. 5ラウンド後も失敗が残る場合: `STOP: 5ラウンド後も未解決。result.json を確認してください` を出力して終了する

### Step 6: 完了レポートを出力する

```
クレンジング完了（PDCA Round {N}）
行数: {総行数}  店舗数: {店舗数}  全20項目 PASS
```

---

## 重要な注意事項

- `python` コマンドは `C:\Users\realp\miniconda3\python.exe` を使うこと
- `validate.py` 自体は PDCA ループ中に修正しない
````

- [ ] **Step 6: data-analyst エージェント定義を作成する**

Write `06_restaurant/01_daily_sales/.claude/agents/data-analyst.md`:

````markdown
---
name: data-analyst
description: 飲食店売上・廃棄ロス分析専門エージェント。output/cleaned_sales_202401.csv を読み込み、店舗別サマリー・日次トレンド・廃棄ロス率集計・アラートをまとめた output/analysis_report.md を生成する。全7項目のレポート品質チェックが全PASS するまで自律的に PDCA ループで修正を繰り返す。「分析して」「廃棄ロスを集計して」「data-analyst」と言われたときに使用する。前提: sales-cleaner を先に実行済みであること。
tools:
  - Read
  - Write
  - Bash
---

あなたはビジネスインサイト分析の専門家です。以下の手順で売上・廃棄ロスデータを分析し、全7項目のレポート品質チェックが PASS するまで自律的に修正を繰り返してください。

## Step 1: 前提確認

```bash
C:\Users\realp\miniconda3\python.exe -c "from pathlib import Path; assert Path('output/cleaned_sales_202401.csv').exists(), 'ERROR: sales-cleaner を先に実行してください'; print('OK')"
```

## Step 2: 分析スクリプトを output/analyze.py に書く

Write ツールで以下の内容を `output/analyze.py` に書き込む:

```python
import pandas as pd
import numpy as np
from pathlib import Path

WASTE_ALERT_THRESHOLD = 0.05  # 廃棄ロス率 5% 超でアラート

df = pd.read_csv("output/cleaned_sales_202401.csv", encoding="utf-8-sig")

if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
for col in ["sales_amount", "waste_qty", "waste_amount"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

lines = ["# 売上・廃棄ロス分析レポート（2024年1月）\n"]

# 1. 店舗別サマリー
lines.append("## 1. 店舗別サマリー\n")
store_summary = df.groupby("store_name")["sales_amount"].agg(
    月間合計="sum", 日平均="mean", 最高日売上="max", 最低日売上="min"
).sort_values("月間合計", ascending=False)
store_summary_fmt = store_summary.copy()
store_summary_fmt["月間合計"] = store_summary_fmt["月間合計"].map("{:,.0f}円".format)
store_summary_fmt["日平均"] = store_summary_fmt["日平均"].map("{:,.0f}円".format)
lines.append(store_summary_fmt.to_markdown())
lines.append("")

# 2. 月間売上ランキング
lines.append("## 2. 月間売上ランキング\n")
ranking = df.groupby("store_name")["sales_amount"].sum().sort_values(ascending=False).reset_index()
for i, row in ranking.iterrows():
    lines.append(f"{i+1}. {row['store_name']}: {row['sales_amount']:,.0f}円")
lines.append("")

# 3. 日次トレンド
if "date" in df.columns:
    lines.append("## 3. 日次トレンド\n")
    daily = df.groupby("date")["sales_amount"].sum()
    if len(daily) >= 20:
        first10 = daily.iloc[:10].mean()
        last10 = daily.iloc[-10:].mean()
        change = (last10 - first10) / first10 * 100 if first10 > 0 else 0
        lines.append(f"- 月初10日平均: {first10:,.0f}円")
        lines.append(f"- 月末10日平均: {last10:,.0f}円")
        lines.append(f"- 月初→月末変化率: {change:+.1f}%")
    lines.append("")

# 4. 異常値検出（±2σ）
lines.append("## 4. 異常値検出（±2σ）\n")
anomalies = []
for store, grp in df.groupby("store_name"):
    if "sales_amount" in grp.columns and len(grp) > 2:
        mean = grp["sales_amount"].mean()
        std = grp["sales_amount"].std()
        if std > 0:
            outliers = grp[np.abs(grp["sales_amount"] - mean) > 2 * std]
            for _, row in outliers.iterrows():
                date_str = str(row.get("date", "不明"))[:10]
                anomalies.append(
                    f"- {store} | {date_str} | {row['sales_amount']:,.0f}円"
                    f"（平均 {mean:,.0f}円 から {(row['sales_amount']-mean)/std:+.1f}σ）"
                )
if anomalies:
    lines.extend(anomalies)
else:
    lines.append("- 異常値は検出されませんでした")
lines.append("")

# 5. ビジネスインサイト
lines.append("## 5. ビジネスインサイト\n")
total = df["sales_amount"].sum()
store_totals = df.groupby("store_name")["sales_amount"].sum()
top_store = store_totals.idxmax()
bottom_store = store_totals.idxmin()
top_val = store_totals.max()
bottom_val = store_totals.min()
gap_ratio = top_val / bottom_val if bottom_val > 0 else float("inf")

lines.append(f"- 全店舗1月合計売上: **{total:,.0f}円**")
lines.append(f"- トップ店舗: **{top_store}**（{top_val:,.0f}円）")
lines.append(f"- ボトム店舗: **{bottom_store}**（{bottom_val:,.0f}円）")
lines.append(f"- トップ/ボトム倍率: **{gap_ratio:.1f}倍** — {'格差が大きい' if gap_ratio > 2 else '均衡している'}")
if anomalies:
    lines.append(f"- 異常値が {len(anomalies)} 件検出 — 要因調査を推奨")
lines.append("")

# 6. 廃棄ロス率分析（A-02 追加）
lines.append("## 6. 廃棄ロス率分析\n")
if "waste_amount" in df.columns and "sales_amount" in df.columns:
    waste_summary = df.groupby("store_name").agg(
        売上合計=("sales_amount", "sum"),
        廃棄金額合計=("waste_amount", "sum"),
        廃棄数量合計=("waste_qty", "sum") if "waste_qty" in df.columns else ("waste_amount", "count"),
    )
    waste_summary["廃棄ロス率"] = (
        waste_summary["廃棄金額合計"] / waste_summary["売上合計"] * 100
    ).fillna(0)
    waste_summary_fmt = waste_summary.copy()
    waste_summary_fmt["売上合計"] = waste_summary_fmt["売上合計"].map("{:,.0f}円".format)
    waste_summary_fmt["廃棄金額合計"] = waste_summary_fmt["廃棄金額合計"].map("{:,.0f}円".format)
    waste_summary_fmt["廃棄ロス率"] = waste_summary_fmt["廃棄ロス率"].map("{:.2f}%".format)
    lines.append(waste_summary_fmt.to_markdown())
    lines.append("")

    alert_stores = waste_summary[waste_summary["廃棄ロス率"] > WASTE_ALERT_THRESHOLD * 100]
    if len(alert_stores) > 0:
        lines.append(f"### ⚠️ アラート: 廃棄ロス率 {WASTE_ALERT_THRESHOLD*100:.0f}% 超の店舗")
        for store, row in alert_stores.iterrows():
            lines.append(
                f"- **{store}**: 廃棄ロス率 {row['廃棄ロス率']:.2f}% "
                f"（廃棄金額: {row['廃棄金額合計']:,.0f}円）"
            )
        lines.append("")
    else:
        lines.append(f"- 全店舗の廃棄ロス率は {WASTE_ALERT_THRESHOLD*100:.0f}% 以内で正常範囲です")
        lines.append("")

    # 商品カテゴリ別廃棄ロス
    if "category" in df.columns:
        lines.append("### カテゴリ別廃棄ロス率\n")
        cat_waste = df.groupby("category").agg(
            売上=("sales_amount", "sum"),
            廃棄=("waste_amount", "sum"),
        )
        cat_waste["廃棄ロス率"] = (cat_waste["廃棄"] / cat_waste["売上"] * 100).fillna(0)
        cat_waste = cat_waste.sort_values("廃棄ロス率", ascending=False)
        cat_waste_fmt = cat_waste.copy()
        cat_waste_fmt["廃棄ロス率"] = cat_waste_fmt["廃棄ロス率"].map("{:.2f}%".format)
        lines.append(cat_waste_fmt.to_markdown())
        lines.append("")
else:
    lines.append("- waste_amount 列が見つからないためスキップ")
    lines.append("")

Path("output/analysis_report.md").write_text("\n".join(lines), encoding="utf-8")
print("分析完了: output/analysis_report.md を生成しました")
```

## Step 3: レポート品質チェックスクリプトを output/validate_report.py に書く

Write ツールで以下の内容を `output/validate_report.py` に書き込む:

```python
"""
レポート品質チェックリスト（7項目）- 飲食業 A-02 版
"""
import json
import re
from pathlib import Path

REPORT_PATH = Path("output/analysis_report.md")
CSV_PATH = Path("output/cleaned_sales_202401.csv")
RESULT_PATH = Path("output/result_analysis.json")

results = []


def check(check_id, name, condition, detail="", fix_hint=""):
    status = "PASS" if condition else "FAIL"
    results.append({
        "id": check_id, "name": name, "status": status,
        "detail": "" if condition else detail,
        "fix_hint": "" if condition else fix_hint,
    })
    return condition


check(1, "report_exists", REPORT_PATH.exists(),
      "analysis_report.md が存在しない",
      "analyze.py を再実行する")

if REPORT_PATH.exists():
    text = REPORT_PATH.read_text(encoding="utf-8")

    sections = ["店舗別サマリー", "月間売上ランキング", "日次トレンド", "異常値検出",
                "ビジネスインサイト", "廃棄ロス率分析"]
    missing_sec = [s for s in sections if s not in text]
    check(2, "all_sections_present", len(missing_sec) == 0,
          f"欠落セクション: {missing_sec}",
          "analyze.py の各分析ブロック（## N. セクション名）を確認する")

    if CSV_PATH.exists():
        import pandas as pd
        df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
        stores = df["store_name"].unique().tolist() if "store_name" in df.columns else []
        missing_stores = [s for s in stores if s not in text]
        check(3, "all_stores_in_report", len(missing_stores) == 0,
              f"レポートに未掲載の店舗: {missing_stores}",
              "store_summary / ranking の groupby('store_name') を確認")
    else:
        check(3, "all_stores_in_report", False,
              "cleaned_sales_202401.csv が存在しない",
              "sales-cleaner を先に実行する")

    keywords = ["全店舗", "トップ店舗", "ボトム店舗"]
    missing_kw = [k for k in keywords if k not in text]
    check(4, "insight_keywords", len(missing_kw) == 0,
          f"インサイトセクションに欠落キーワード: {missing_kw}",
          "analyze.py の '5. ビジネスインサイト' セクションを確認")

    anomaly_match = re.search(r"## 4.*?(?=## 5|\Z)", text, re.DOTALL)
    anomaly_lines = len(anomaly_match.group(0).strip().splitlines()) if anomaly_match else 0
    check(5, "anomaly_section_content", anomaly_lines >= 3,
          f"異常値検出セクションが薄い（{anomaly_lines}行）",
          "analyze.py の ±2σ 異常値検出ロジックを確認")

    has_numbers = bool(re.search(r"\d{1,3}(,\d{3})+円", text))
    check(6, "numeric_values_present", has_numbers,
          "レポートに金額（例: 1,234,567円）が含まれない",
          "analyze.py の format 処理（{:,.0f}円）を確認")

    waste_section_ok = "廃棄ロス率" in text and "%" in text
    check(7, "waste_loss_section", waste_section_ok,
          "廃棄ロス率セクションが存在しないか内容が空",
          "analyze.py の '6. 廃棄ロス率分析' セクションを確認")

else:
    for i in range(2, 8):
        results.append({
            "id": i, "name": f"check_{i}", "status": "FAIL",
            "detail": "レポートが存在しないためスキップ",
            "fix_hint": "analyze.py を実行してレポートを生成する",
        })

passed = sum(1 for r in results if r["status"] == "PASS")
failed = len(results) - passed
output = {"passed": passed, "failed": failed, "all_passed": failed == 0, "results": results}
RESULT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n{'='*48}")
print(f"  レポート品質チェック: {passed}/{len(results)} PASS")
print(f"{'='*48}")
for r in results:
    icon = "PASS" if r["status"] == "PASS" else "FAIL"
    line = f"  [{icon}] #{r['id']:02d} {r['name']}"
    if r["detail"]:
        line += f"\n         -> {r['detail']}"
        line += f"\n         HINT: {r['fix_hint']}"
    print(line)

if failed == 0:
    print("\n  全7項目クリア!")
else:
    print(f"\n  {failed}項目が失敗。result_analysis.json の fix_hint を参照してください。")
```

## Step 4: PDCA ループ（最大3ラウンド）

1. `C:\Users\realp\miniconda3\python.exe output/analyze.py` を実行する
2. `C:\Users\realp\miniconda3\python.exe output/validate_report.py` を実行する
3. `output/result_analysis.json` を Read ツールで読み込む
4. `"all_passed"` が `true` → Step 5 へ進む
5. `"all_passed"` が `false` の場合: `"status": "FAIL"` の項目の `fix_hint` を参照して `output/analyze.py` を修正する
6. 3ラウンド後も失敗が残る場合: `STOP` を出力して終了する

## Step 5: 完了レポートを出力する

```
分析完了（PDCA Round {N}）
全7項目 PASS → output/analysis_report.md を確認してください
```

---

## 重要な注意事項

- `python` コマンドは `C:\Users\realp\miniconda3\python.exe` を使うこと
- `validate_report.py` 自体は PDCA ループ中に修正しない
````

- [ ] **Step 7: サンプルデータ生成スクリプトを作成して実行する**

Write `06_restaurant/01_daily_sales/_gen_sample_data.py`:

```python
"""
A-02 サンプルデータ生成スクリプト（5店舗・3列名バリエーション）
実行: C:\Users\realp\miniconda3\python.exe _gen_sample_data.py
"""
import pandas as pd
import random
from pathlib import Path

random.seed(42)
out = Path(".")

categories = ["麺類", "ご飯もの", "副菜", "ドリンク", "デザート"]
items_by_cat = {
    "麺類":    [("ラーメン", 900), ("つけ麺", 1000), ("担々麺", 980), ("塩ラーメン", 880)],
    "ご飯もの": [("チャーハン", 750), ("カレーライス", 800), ("天丼", 950)],
    "副菜":    [("餃子", 450), ("唐揚げ", 550), ("春巻き", 400)],
    "ドリンク": [("ウーロン茶", 250), ("コーラ", 300), ("ビール", 550)],
    "デザート": [("杏仁豆腐", 380), ("アイスクリーム", 400)],
}


def gen_rows(store_name, n=120, col_style="standard"):
    rows = []
    for _ in range(n):
        day = random.randint(1, 28)
        date_str = f"2024/01/{day:02d}"
        cat = random.choice(categories)
        item, price = random.choice(items_by_cat[cat])
        qty = random.randint(1, 8)
        sales = qty * price
        waste_qty = random.choices([0, 1, 2], weights=[0.7, 0.2, 0.1])[0]
        waste_amount = waste_qty * price

        if col_style == "standard":
            rows.append({"日付": date_str, "店舗名": store_name, "商品名": item,
                         "カテゴリ": cat, "数量": qty, "単価": price, "売上金額": sales,
                         "廃棄数量": waste_qty, "廃棄金額": waste_amount})
        elif col_style == "english":
            rows.append({"Date": date_str, "Store": store_name, "Item": item,
                         "Category": cat, "Qty": qty, "Price": price, "Sales": sales,
                         "WasteQty": waste_qty, "WasteAmount": waste_amount})
        elif col_style == "variant":
            rows.append({"日付け": date_str, "店舗": store_name, "品名": item,
                         "分類": cat, "個数": qty, "単価": price, "売上額": sales,
                         "廃棄": waste_qty, "廃棄金額": waste_amount})
    return rows


stores = [
    ("渋谷店", "standard", "01_渋谷店_売上_202401.csv"),
    ("新宿店", "english",  "02_新宿店_売上_202401.csv"),
    ("池袋店", "variant",  "03_池袋店_売上_202401.csv"),
    ("横浜店", "standard", "04_横浜店_売上_202401.csv"),
    ("大阪店", "standard", "05_大阪店_売上_202401.csv"),
]

for store_name, style, filename in stores:
    n = random.randint(110, 150)
    rows = gen_rows(store_name, n=n, col_style=style)
    df = pd.DataFrame(rows)
    df.to_csv(out / filename, index=False, encoding="utf-8-sig")
    print(f"Created {filename}: {len(df)} rows, style={style}")

print("\nサンプルデータ生成完了（5店舗）")
```

実行コマンド:
```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\06_restaurant\01_daily_sales
C:\Users\realp\miniconda3\python.exe _gen_sample_data.py
```

期待出力:
```
Created 01_渋谷店_売上_202401.csv: 124 rows, style=standard
Created 02_新宿店_売上_202401.csv: 118 rows, style=english
Created 03_池袋店_売上_202401.csv: 143 rows, style=variant
Created 04_横浜店_売上_202401.csv: 131 rows, style=standard
Created 05_大阪店_売上_202401.csv: 112 rows, style=standard
サンプルデータ生成完了（5店舗）
```

5つの CSV ファイルが生成されることを確認する。

- [ ] **Step 8: 初回コミット**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio
git add 06_restaurant/
git commit -m "feat: scaffold A-02 restaurant daily sales and waste loss pipeline"
```

---

## Task 2: クレンジング + バリデーション実行（PDCA）

**Files:**
- Generate: `06_restaurant/01_daily_sales/output/cleanse.py` (Task 1 の agent 定義から生成)
- Generate: `06_restaurant/01_daily_sales/output/validate.py` (Task 1 の agent 定義から生成)
- Generate: `06_restaurant/01_daily_sales/output/cleaned_sales_202401.csv`

- [ ] **Step 1: sales-cleaner エージェントを起動してクレンジングを実行する**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\06_restaurant\01_daily_sales
# Claude Code でエージェントを起動:
# /agent:sales-cleaner クレンジングして
```

エージェントが `output/cleanse.py` と `output/validate.py` を生成し、PDCA ループで全20項目 PASS を達成することを確認する。

- [ ] **Step 2: 出力を確認する**

```bash
C:\Users\realp\miniconda3\python.exe -c "
import pandas as pd
df = pd.read_csv('output/cleaned_sales_202401.csv', encoding='utf-8-sig')
print('行数:', len(df))
print('店舗数:', df['store_name'].nunique())
print('列:', list(df.columns))
print('廃棄ロス確認:')
print(df[['waste_qty','waste_amount']].describe())
"
```

期待出力:
```
行数: 600 前後（500〜1200 の範囲内）
店舗数: 5
列: ['date', 'store_name', 'item_name', 'category', 'quantity', 'unit_price', 'sales_amount', 'waste_qty', 'waste_amount', 'sales_imputed', 'source_file']
廃棄ロス確認:
       waste_qty  waste_amount
count   628.000    628.000
mean      0.XXX     XXX.XXX
...
```

`waste_qty` と `waste_amount` 列が存在することを確認する。

- [ ] **Step 3: コミット**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio
git add 06_restaurant/01_daily_sales/output/
git commit -m "feat: A-02 cleansing complete, all 20 checks passed"
```

---

## Task 3: 分析 + レポート品質チェック実行（PDCA）

**Files:**
- Generate: `06_restaurant/01_daily_sales/output/analyze.py`
- Generate: `06_restaurant/01_daily_sales/output/validate_report.py`
- Generate: `06_restaurant/01_daily_sales/output/analysis_report.md`

- [ ] **Step 1: data-analyst エージェントを起動して分析を実行する**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\06_restaurant\01_daily_sales
# Claude Code でエージェントを起動:
# /agent:data-analyst 廃棄ロスを集計して
```

エージェントが `output/analyze.py` と `output/validate_report.py` を生成し、PDCA ループで全7項目 PASS を達成することを確認する。

- [ ] **Step 2: レポート内容を確認する**

```bash
C:\Users\realp\miniconda3\python.exe -c "
from pathlib import Path
text = Path('output/analysis_report.md').read_text(encoding='utf-8')
# セクション確認
for sec in ['店舗別サマリー', '廃棄ロス率分析', 'アラート']:
    print(f'{sec}: {\"OK\" if sec in text else \"MISSING\"}')"
```

期待出力:
```
店舗別サマリー: OK
廃棄ロス率分析: OK
アラート: OK（廃棄ロス率 5% 超の店舗がある場合）
```

- [ ] **Step 3: コミット**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio
git add 06_restaurant/01_daily_sales/output/
git commit -m "feat: A-02 analysis complete, waste loss rate report generated"
```

---

## Task 4: 可視化スクリプト + エージェント定義

**Files:**
- Create: `06_restaurant/01_daily_sales/.claude/agents/data-viz-engineer.md`
- Generate: `06_restaurant/01_daily_sales/output/visualize.py`
- Generate: `06_restaurant/01_daily_sales/output/charts/*.png`

- [ ] **Step 1: data-viz-engineer エージェント定義を作成する**

Write `06_restaurant/01_daily_sales/.claude/agents/data-viz-engineer.md`:

````markdown
---
name: data-viz-engineer
description: 飲食店売上・廃棄ロス可視化専門エージェント。output/cleaned_sales_202401.csv と output/analysis_report.md を読み込み、棒グラフ（店舗別売上）・折れ線グラフ（日次トレンド）・廃棄ロス率棒グラフを output/charts/ に出力する。「グラフを作って」「可視化して」「data-viz-engineer」と言われたときに使用する。前提: data-analyst を先に実行済みであること。
tools:
  - Read
  - Write
  - Bash
---

あなたはデータ可視化の専門家です。以下の手順でグラフを生成してください。

## Step 1: 前提確認

```bash
C:\Users\realp\miniconda3\python.exe -c "from pathlib import Path; assert Path('output/cleaned_sales_202401.csv').exists(); print('OK')"
```

## Step 2: visualize.py を output/visualize.py に書く

Write ツールで以下の内容を `output/visualize.py` に書き込む:

```python
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import japanize_matplotlib
from pathlib import Path

df = pd.read_csv("output/cleaned_sales_202401.csv", encoding="utf-8-sig")
for col in ["sales_amount", "waste_amount"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

charts_dir = Path("output/charts")
charts_dir.mkdir(exist_ok=True)

# 1. 店舗別売上棒グラフ
store_sales = df.groupby("store_name")["sales_amount"].sum().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(store_sales.index, store_sales.values, color="#2563eb")
ax.set_title("店舗別月間売上（2024年1月）", fontsize=14)
ax.set_ylabel("売上金額（円）")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
for bar in bars:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h + h*0.01,
            f"{h:,.0f}", ha="center", va="bottom", fontsize=10)
plt.tight_layout()
plt.savefig(charts_dir / "bar_store_sales.png", dpi=150)
plt.close()
print("Saved: bar_store_sales.png")

# 2. 日次売上折れ線グラフ
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    daily = df.groupby("date")["sales_amount"].sum().sort_index()
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(daily.index, daily.values, marker="o", color="#2563eb", linewidth=2, markersize=4)
    ax.set_title("日次売上トレンド（2024年1月）", fontsize=14)
    ax.set_ylabel("売上金額（円）")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(charts_dir / "line_daily_sales.png", dpi=150)
    plt.close()
    print("Saved: line_daily_sales.png")

# 3. 廃棄ロス率棒グラフ（A-02 追加）
if "waste_amount" in df.columns:
    waste = df.groupby("store_name").agg(
        売上=("sales_amount", "sum"),
        廃棄=("waste_amount", "sum"),
    )
    waste["廃棄ロス率"] = waste["廃棄"] / waste["売上"] * 100
    waste = waste.sort_values("廃棄ロス率", ascending=False)

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ["#ef4444" if v > 5 else "#22c55e" for v in waste["廃棄ロス率"]]
    bars = ax.bar(waste.index, waste["廃棄ロス率"], color=colors)
    ax.axhline(y=5, color="red", linestyle="--", linewidth=1.5, label="アラート閾値（5%）")
    ax.set_title("店舗別廃棄ロス率（2024年1月）", fontsize=14)
    ax.set_ylabel("廃棄ロス率（%）")
    for bar, v in zip(bars, waste["廃棄ロス率"]):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.1,
                f"{v:.2f}%", ha="center", va="bottom", fontsize=10)
    ax.legend()
    plt.tight_layout()
    plt.savefig(charts_dir / "bar_waste_loss.png", dpi=150)
    plt.close()
    print("Saved: bar_waste_loss.png")

print("グラフ生成完了")
```

## Step 3: visualize.py を実行する

```bash
C:\Users\realp\miniconda3\python.exe output/visualize.py
```

期待出力:
```
Saved: bar_store_sales.png
Saved: line_daily_sales.png
Saved: bar_waste_loss.png
グラフ生成完了
```

## Step 4: ファイル存在を確認する

```bash
C:\Users\realp\miniconda3\python.exe -c "
from pathlib import Path
for p in ['output/charts/bar_store_sales.png', 'output/charts/line_daily_sales.png', 'output/charts/bar_waste_loss.png']:
    print(p, ':', 'OK' if Path(p).exists() else 'MISSING')"
```

全ファイルが `OK` であることを確認する。

## 重要な注意事項

- `python` コマンドは `C:\Users\realp\miniconda3\python.exe` を使うこと
- `japanize_matplotlib` がない場合: `pip install japanize-matplotlib` を実行する
````

- [ ] **Step 2: data-viz-engineer エージェントを起動してグラフを生成する**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\06_restaurant\01_daily_sales
# Claude Code でエージェントを起動:
# /agent:data-viz-engineer グラフを作って
```

`output/charts/bar_store_sales.png`, `line_daily_sales.png`, `bar_waste_loss.png` の3ファイルが生成されることを確認する。

- [ ] **Step 3: コミット**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio
git add 06_restaurant/01_daily_sales/
git commit -m "feat: A-02 visualization complete, waste loss chart added"
```

---

## Task 5: Streamlit アプリ (app.py)

**Files:**
- Create: `06_restaurant/01_daily_sales/app.py`

- [ ] **Step 1: app.py を作成する**

Write `06_restaurant/01_daily_sales/app.py`:

```python
"""
A-02 飲食×日次売上・廃棄ロス集計レポート
起動: streamlit run app.py
"""
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="飲食×廃棄ロスレポート",
    page_icon="🍜",
    layout="wide",
)

CSV_PATH = Path("output/cleaned_sales_202401.csv")
REPORT_PATH = Path("output/analysis_report.md")
CHARTS = {
    "店舗別月間売上": Path("output/charts/bar_store_sales.png"),
    "日次売上トレンド": Path("output/charts/line_daily_sales.png"),
    "廃棄ロス率": Path("output/charts/bar_waste_loss.png"),
}

WASTE_THRESHOLD = 0.05


@st.cache_data
def load_data():
    if not CSV_PATH.exists():
        return None
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    for col in ["sales_amount", "waste_qty", "waste_amount"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def main():
    st.title("🍜 飲食×日次売上・廃棄ロス集計レポート")
    st.caption("A-02 | 5店舗 | 2024年1月 | Sub-agents Pipeline")

    df = load_data()

    if df is None:
        st.error("データが見つかりません。`python run_pipeline.py` を実行してください。")
        return

    # ── メトリクス ──────────────────────────────────────
    store_agg = df.groupby("store_name").agg(
        売上=("sales_amount", "sum"),
        廃棄=("waste_amount", "sum"),
    )
    store_agg["廃棄ロス率"] = store_agg["廃棄"] / store_agg["売上"] * 100

    total_sales = df["sales_amount"].sum()
    total_waste = df["waste_amount"].sum()
    avg_waste_rate = total_waste / total_sales * 100 if total_sales > 0 else 0
    alert_count = (store_agg["廃棄ロス率"] > WASTE_THRESHOLD * 100).sum()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("店舗数", f"{df['store_name'].nunique()} 店")
    c2.metric("月間売上合計", f"¥{total_sales:,.0f}")
    c3.metric("廃棄金額合計", f"¥{total_waste:,.0f}")
    c4.metric("平均廃棄ロス率", f"{avg_waste_rate:.2f}%",
              delta=f"{avg_waste_rate - WASTE_THRESHOLD*100:+.2f}pp vs 閾値",
              delta_color="inverse")
    c5.metric("⚠️ アラート店舗", f"{alert_count} 店")

    st.divider()

    # ── グラフ ──────────────────────────────────────────
    st.subheader("グラフ")
    tabs = st.tabs(list(CHARTS.keys()))
    for tab, (title, path) in zip(tabs, CHARTS.items()):
        with tab:
            if path.exists():
                st.image(str(path), use_container_width=True)
            else:
                st.warning(f"{path} が見つかりません。`run_pipeline.py` を実行してください。")

    st.divider()

    # ── 廃棄ロス率テーブル ───────────────────────────────
    st.subheader("廃棄ロス率 店舗別サマリー")
    display = store_agg.copy()
    display["売上"] = display["売上"].map("¥{:,.0f}".format)
    display["廃棄"] = display["廃棄"].map("¥{:,.0f}".format)
    display["廃棄ロス率"] = display["廃棄ロス率"].map("{:.2f}%".format)
    st.dataframe(display, use_container_width=True)

    st.divider()

    # ── 詳細データ（フィルタ） ──────────────────────────
    st.subheader("詳細データ")
    stores = ["全店舗"] + sorted(df["store_name"].unique().tolist())
    sel = st.selectbox("店舗", stores)
    filt = df if sel == "全店舗" else df[df["store_name"] == sel]
    st.caption(f"{len(filt)} 件")
    st.dataframe(filt, use_container_width=True, height=300)

    st.divider()

    # ── 分析レポート ────────────────────────────────────
    if REPORT_PATH.exists():
        st.subheader("分析レポート (Markdown)")
        with st.expander("レポートを表示", expanded=False):
            st.markdown(REPORT_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Streamlit を起動して動作確認する**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\06_restaurant\01_daily_sales
.venv\Scripts\streamlit run app.py
# または: C:\Users\realp\miniconda3\Scripts\streamlit.exe run app.py
```

ブラウザで確認すること:
- メトリクスカード（5店舗・売上合計・廃棄金額・廃棄ロス率・アラート店舗数）が表示される
- グラフタブが3つある（店舗別売上・日次トレンド・廃棄ロス率）
- 廃棄ロス率テーブルが表示される
- 店舗フィルタで絞り込みができる

- [ ] **Step 3: コミット**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio
git add 06_restaurant/01_daily_sales/app.py
git commit -m "feat: A-02 Streamlit app with waste loss dashboard"
```

---

## Task 6: テスト

**Files:**
- Create: `06_restaurant/01_daily_sales/tests/test_cleaner_output.py`
- Create: `06_restaurant/01_daily_sales/tests/test_analyst_output.py`
- Create: `06_restaurant/01_daily_sales/tests/test_viz_output.py`

- [ ] **Step 1: クレンジング出力テストを作成する**

Write `06_restaurant/01_daily_sales/tests/test_cleaner_output.py`:

```python
"""
A-02 クレンジング出力テスト
実行: cd 06_restaurant/01_daily_sales && pytest tests/test_cleaner_output.py -v
前提: python run_pipeline.py を実行済みであること
"""
import pytest
import pandas as pd
from pathlib import Path

CSV_PATH = Path("output/cleaned_sales_202401.csv")
RESULT_PATH = Path("output/result.json")

REQUIRED_COLS = [
    "date", "store_name", "item_name", "category",
    "quantity", "unit_price", "sales_amount",
    "waste_qty", "waste_amount",
    "sales_imputed", "source_file",
]
EXPECTED_STORES = {"渋谷店", "新宿店", "池袋店", "横浜店", "大阪店"}


@pytest.fixture(scope="module")
def df():
    assert CSV_PATH.exists(), f"{CSV_PATH} が存在しない。run_pipeline.py を実行してください"
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def test_csv_exists():
    assert CSV_PATH.exists()


def test_required_columns(df):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    assert missing == [], f"欠落列: {missing}"


def test_store_count(df):
    actual = set(df["store_name"].unique())
    assert actual == EXPECTED_STORES, f"期待: {EXPECTED_STORES}, 実際: {actual}"


def test_row_count(df):
    assert 500 <= len(df) <= 1200, f"行数 {len(df)} が範囲外（500〜1200）"


def test_no_null_dates(df):
    null_count = df["date"].isna().sum()
    assert null_count == 0, f"date に NaN が {null_count} 件"


def test_date_format(df):
    bad = df["date"].dropna()[~df["date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")]
    assert len(bad) == 0, f"YYYY-MM-DD 形式でない日付: {len(bad)} 件"


def test_date_in_january_2024(df):
    out = df["date"].dropna()[~df["date"].dropna().str.startswith("2024-01")]
    assert len(out) == 0, f"2024-01 以外の日付: {len(out)} 件"


def test_sales_amount_nonnegative(df):
    neg = (df["sales_amount"] < 0).sum()
    assert neg == 0, f"sales_amount < 0: {neg} 件"


def test_waste_qty_column_exists(df):
    assert "waste_qty" in df.columns, "waste_qty 列が存在しない"


def test_waste_amount_column_exists(df):
    assert "waste_amount" in df.columns, "waste_amount 列が存在しない"


def test_waste_qty_nonnegative(df):
    if "waste_qty" in df.columns:
        neg = (df["waste_qty"] < 0).sum()
        assert neg == 0, f"waste_qty < 0: {neg} 件"


def test_waste_amount_nonnegative(df):
    if "waste_amount" in df.columns:
        neg = (df["waste_amount"] < 0).sum()
        assert neg == 0, f"waste_amount < 0: {neg} 件"


def test_no_duplicates(df):
    dup = df.duplicated().sum()
    assert dup == 0, f"重複行: {dup} 件"


def test_all_validate_checks_passed():
    import json
    assert RESULT_PATH.exists(), "result.json が存在しない"
    data = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    assert data["all_passed"], (
        f"validate.py が全PASS していない: "
        f"{[r for r in data['results'] if r['status'] == 'FAIL']}"
    )
```

- [ ] **Step 2: テストを実行して PASS することを確認する**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\06_restaurant\01_daily_sales
C:\Users\realp\miniconda3\python.exe -m pytest tests/test_cleaner_output.py -v
```

期待出力（全テスト PASS）:
```
PASSED tests/test_cleaner_output.py::test_csv_exists
PASSED tests/test_cleaner_output.py::test_required_columns
PASSED tests/test_cleaner_output.py::test_store_count
PASSED tests/test_cleaner_output.py::test_row_count
PASSED tests/test_cleaner_output.py::test_no_null_dates
PASSED tests/test_cleaner_output.py::test_date_format
PASSED tests/test_cleaner_output.py::test_date_in_january_2024
PASSED tests/test_cleaner_output.py::test_sales_amount_nonnegative
PASSED tests/test_cleaner_output.py::test_waste_qty_column_exists
PASSED tests/test_cleaner_output.py::test_waste_amount_column_exists
PASSED tests/test_cleaner_output.py::test_waste_qty_nonnegative
PASSED tests/test_cleaner_output.py::test_waste_amount_nonnegative
PASSED tests/test_cleaner_output.py::test_no_duplicates
PASSED tests/test_cleaner_output.py::test_all_validate_checks_passed
14 passed in X.XXs
```

- [ ] **Step 3: 分析レポートテストを作成して実行する**

Write `06_restaurant/01_daily_sales/tests/test_analyst_output.py`:

```python
"""
A-02 分析レポートテスト
実行: cd 06_restaurant/01_daily_sales && pytest tests/test_analyst_output.py -v
"""
import json
import re
import pytest
from pathlib import Path

REPORT_PATH = Path("output/analysis_report.md")
RESULT_PATH = Path("output/result_analysis.json")

EXPECTED_SECTIONS = [
    "店舗別サマリー", "月間売上ランキング", "日次トレンド",
    "異常値検出", "ビジネスインサイト", "廃棄ロス率分析",
]


@pytest.fixture(scope="module")
def report_text():
    assert REPORT_PATH.exists(), "analysis_report.md が存在しない。data-analyst エージェントを実行してください"
    return REPORT_PATH.read_text(encoding="utf-8")


def test_report_exists():
    assert REPORT_PATH.exists()


def test_all_sections_present(report_text):
    missing = [s for s in EXPECTED_SECTIONS if s not in report_text]
    assert missing == [], f"欠落セクション: {missing}"


def test_waste_loss_rate_in_report(report_text):
    assert "廃棄ロス率" in report_text, "廃棄ロス率の記載がない"


def test_percentage_values_present(report_text):
    has_pct = bool(re.search(r"\d+\.\d+%", report_text))
    assert has_pct, "廃棄ロス率（XX.XX%形式）が含まれない"


def test_monetary_values_present(report_text):
    has_money = bool(re.search(r"\d{1,3}(,\d{3})+円", report_text))
    assert has_money, "金額（1,234,567円形式）が含まれない"


def test_all_report_checks_passed():
    assert RESULT_PATH.exists(), "result_analysis.json が存在しない"
    data = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    assert data["all_passed"], (
        f"validate_report.py が全PASS していない: "
        f"{[r for r in data['results'] if r['status'] == 'FAIL']}"
    )
```

実行コマンド:
```bash
C:\Users\realp\miniconda3\python.exe -m pytest tests/test_analyst_output.py -v
```

期待出力: `6 passed`

- [ ] **Step 4: 可視化テストを作成して実行する**

Write `06_restaurant/01_daily_sales/tests/test_viz_output.py`:

```python
"""
A-02 可視化テスト
実行: cd 06_restaurant/01_daily_sales && pytest tests/test_viz_output.py -v
"""
import pytest
from pathlib import Path

CHARTS = {
    "bar_store_sales": Path("output/charts/bar_store_sales.png"),
    "line_daily_sales": Path("output/charts/line_daily_sales.png"),
    "bar_waste_loss": Path("output/charts/bar_waste_loss.png"),
}


def test_bar_store_sales_exists():
    assert CHARTS["bar_store_sales"].exists(), "bar_store_sales.png が存在しない"


def test_line_daily_sales_exists():
    assert CHARTS["line_daily_sales"].exists(), "line_daily_sales.png が存在しない"


def test_bar_waste_loss_exists():
    assert CHARTS["bar_waste_loss"].exists(), "bar_waste_loss.png が存在しない（廃棄ロス率グラフ）"


def test_chart_file_sizes():
    for name, path in CHARTS.items():
        if path.exists():
            size = path.stat().st_size
            assert size > 10_000, f"{name}.png のファイルサイズが小さすぎる（{size} bytes）"
```

実行コマンド:
```bash
C:\Users\realp\miniconda3\python.exe -m pytest tests/test_viz_output.py -v
```

期待出力: `4 passed`

- [ ] **Step 5: 全テストをまとめて実行する**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\06_restaurant\01_daily_sales
C:\Users\realp\miniconda3\python.exe -m pytest tests/ -v
```

期待出力: `24 passed`（全テスト PASS）

- [ ] **Step 6: コミット**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio
git add 06_restaurant/01_daily_sales/tests/
git commit -m "feat: A-02 pytest tests for cleaner/analyst/viz output"
```

---

## Task 7: カタログ更新 + 最終コミット

**Files:**
- Modify: `catalog.yml` (A-02 の status と path を更新)

- [ ] **Step 1: catalog.yml の A-02 エントリを更新する**

`catalog.yml` の A-02 エントリ（飲食セクション）を以下に更新する:

```yaml
- id: "A-02"
  name: "日次売上・廃棄ロス集計レポート"
  industry: "飲食"
  department: "営業・販売"
  status: "production-ready"
  priority: "A"
  path: "06_restaurant/01_daily_sales"
  description: "日次売上と廃棄数量を店舗別・商品別に集計し、廃棄ロス率が閾値超えでアラート。A-01（小売売上分析）からの転用（★★★）"
  demo: "streamlit run app.py"
```

- [ ] **Step 2: ダッシュボードを起動して A-02 が Production-ready で表示されることを確認する**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio
.venv\Scripts\streamlit run dashboard.py
```

ダッシュボードで確認すること:
- メトリクスの「✅ 完成」が 1→2 になっている（A-01 + A-02）
- 飲食×営業・販売 のセルが青くなっている
- タスクリストで A-02 が `✅ Production-ready` と表示される

- [ ] **Step 3: 最終コミット**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio
git add catalog.yml
git commit -m "feat: A-02 complete — restaurant daily sales + waste loss report production-ready"
```

---

## セルフレビュー

### スペックカバレッジ確認

| 要件 | 対応タスク | 状態 |
|------|-----------|------|
| 5店舗の CSV クレンジング | Task 1-2 (cleanse.py) | ✅ |
| 3種類の列名バリエーション対応 | Task 1 (サンプルデータ) | ✅ |
| 廃棄数量・廃棄金額列の統合 | Task 1 (COLUMN_MAP) | ✅ |
| 廃棄ロス率計算（5% 超でアラート） | Task 3 (analyze.py) | ✅ |
| 全20項目バリデーション | Task 2 (validate.py) | ✅ |
| 全7項目レポート品質チェック | Task 3 (validate_report.py) | ✅ |
| 廃棄ロス率棒グラフ | Task 4 (visualize.py) | ✅ |
| Streamlit Web アプリ | Task 5 (app.py) | ✅ |
| pytest テスト | Task 6 (tests/) | ✅ |
| catalog.yml ステータス更新 | Task 7 | ✅ |
| ポートフォリオダッシュボード反映 | Task 7 | ✅ |

### PDCA ループ確認

- cleaner: 最大5ラウンド、validate.py (20項目) が全PASS するまで自律修正
- analyst: 最大3ラウンド、validate_report.py (7項目) が全PASS するまで自律修正
- viz: A-01 と同構造（validate なし、生成確認のみ）

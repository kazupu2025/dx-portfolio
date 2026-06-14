# A-03 在庫データクレンジング・欠品検知 実装プラン

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 物流5倉庫の在庫データをクレンジング・分析し、欠品品目を検知してアラート表示するStreamlitダッシュボードを構築する

**Architecture:** A-02（飲食×売上）と同一のPipelineパターン。在庫特有のCOLUMN_MAP・欠品検知ロジック・在庫可視化グラフに差し替える。cleanse → analyze → visualize → Streamlit app の4ステップパイプラインを `run_pipeline.py` が順次実行する。

**Tech Stack:** Python 3.13, pandas, matplotlib, japanize_matplotlib, streamlit, pyyaml, pytest

---

## ファイルマップ

```
05_logistics/01_inventory/
├── config.yml                       # 閾値・パラメータ定義（新規）
├── run_pipeline.py                  # パイプライン実行スクリプト（新規）
├── app.py                           # Streamlit ダッシュボード（新規）
├── STATUS.md                        # システムステータス（新規）
├── _gen_sample_data.py              # サンプルデータ生成（新規、5倉庫×3スタイル）
├── .claude/agents/
│   ├── inventory-cleaner.md         # クレンジングエージェント定義（新規）
│   └── data-analyst.md              # 分析エージェント定義（新規）
│   └── data-viz-engineer.md         # 可視化エージェント定義（新規, Task 4で追加）
├── output/
│   ├── .gitkeep                     # ディレクトリ保持用
│   ├── cleanse.py                   # [生成物] クレンジングスクリプト
│   ├── validate.py                  # [生成物] クレンジング品質チェック（18項目）
│   ├── analyze.py                   # [生成物] 在庫分析スクリプト
│   ├── validate_report.py           # [生成物] レポート品質チェック（7項目）
│   ├── visualize.py                 # [生成物] グラフ生成スクリプト
│   ├── cleaned_inventory_202401.csv # [生成物] クレンジング済みCSV
│   ├── analysis_report.md           # [生成物] 分析レポート
│   └── charts/
│       ├── bar_warehouse_stock.png  # [生成物] 倉庫別在庫金額棒グラフ
│       ├── bar_stockout_items.png   # [生成物] 倉庫別欠品品目数棒グラフ（赤棒）
│       └── scatter_turnover.png     # [生成物] 品目別在庫回転率散布図
└── tests/
    ├── __init__.py
    ├── test_cleaner_output.py       # クレンジング結果テスト（14テスト）
    ├── test_analyst_output.py       # 分析レポートテスト（6テスト）
    └── test_viz_output.py           # グラフ存在テスト（4テスト）
```

---

## Task 1: ディレクトリ・設定・エージェント定義・サンプルデータ

**Files:**
- Create: `05_logistics/01_inventory/config.yml`
- Create: `05_logistics/01_inventory/STATUS.md`
- Create: `05_logistics/01_inventory/run_pipeline.py`
- Create: `05_logistics/01_inventory/_gen_sample_data.py`
- Create: `05_logistics/01_inventory/.claude/agents/inventory-cleaner.md`
- Create: `05_logistics/01_inventory/.claude/agents/data-analyst.md`
- Create: `05_logistics/01_inventory/output/.gitkeep`

---

- [ ] **Step 1-1: ディレクトリ構造を作成する**

```
C:\Users\realp\miniconda3\python.exe -c "
import pathlib
base = pathlib.Path('C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/05_logistics/01_inventory')
for d in [
    base,
    base / 'output' / 'charts',
    base / '.claude' / 'agents',
    base / 'tests',
    base / 'docs' / 'superpowers' / 'plans',
]:
    d.mkdir(parents=True, exist_ok=True)
    print('OK:', d)
"
```

期待出力: 各ディレクトリパスに続けて `OK:` が表示される

---

- [ ] **Step 1-2: `output/.gitkeep` を作成する**

```
C:\Users\realp\miniconda3\python.exe -c "
from pathlib import Path
p = Path('C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/05_logistics/01_inventory/output/.gitkeep')
p.touch()
print('OK:', p)
"
```

---

- [ ] **Step 1-3: `config.yml` を作成する**

`C:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\05_logistics\01_inventory\config.yml` に書き込む:

```yaml
expected_warehouse_count: 5
expected_year: 2024
expected_month: 1
min_rows: 400
max_rows: 1000
max_imputed_ratio: 0.15
stockout_alert_threshold: 0
low_stock_ratio_threshold: 0.20
```

---

- [ ] **Step 1-4: `STATUS.md` を作成する**

`C:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\05_logistics\01_inventory\STATUS.md` に書き込む:

```markdown
# A-03 在庫データクレンジング・欠品検知

| 項目 | 値 |
|------|-----|
| name | 在庫データクレンジング・欠品検知 |
| industry | 物流・倉庫 |
| status | designing |
| started | 2026-06-14 |
```

---

- [ ] **Step 1-5: `run_pipeline.py` を作成する**

`C:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\05_logistics\01_inventory\run_pipeline.py` に書き込む:

```python
"""
物流×在庫データパイプライン実行スクリプト
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


run("output/cleanse.py",         "Step 1: データクレンジング")
run("output/validate.py",        "Step 2: クレンジング品質チェック（18項目）")
run("output/analyze.py",         "Step 3: 在庫分析・欠品検知")
run("output/validate_report.py", "Step 4: レポート品質チェック（7項目）")
run("output/visualize.py",       "Step 5: グラフ生成")
print("\nパイプライン完了! streamlit run app.py で結果を確認してください")
```

---

- [ ] **Step 1-6: `_gen_sample_data.py` を作成する**

`C:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\05_logistics\01_inventory\_gen_sample_data.py` に書き込む:

```python
"""
A-03 サンプルデータ生成スクリプト（5倉庫・3列名バリエーション）
実行: C:\Users\realp\miniconda3\python.exe _gen_sample_data.py
"""
import pandas as pd
import random
from pathlib import Path

random.seed(42)
out = Path("C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/05_logistics/01_inventory")

categories = ["食料品", "日用品", "電子部品", "衣料品", "工業用品"]
items_by_cat = {
    "食料品":   [("コメ25kg", 8000, 50), ("小麦粉20kg", 4500, 30), ("食用油18L", 3200, 20), ("砂糖50kg", 6000, 15)],
    "日用品":   [("洗剤業務用", 2800, 40), ("ティッシュ箱", 1200, 80), ("トイレットペーパー", 1500, 60)],
    "電子部品": [("基板A型", 15000, 5), ("センサーB型", 8500, 8), ("ケーブル10m", 2200, 25), ("コネクタC", 450, 100)],
    "衣料品":   [("作業着M", 4200, 10), ("安全靴26cm", 6800, 8), ("手袋L", 320, 200)],
    "工業用品": [("ボルトM6×50", 120, 500), ("グリース缶", 1800, 30), ("切削油5L", 2500, 20)],
}


def gen_rows(warehouse_name: str, n: int = 120, col_style: str = "standard") -> list:
    rows = []
    for _ in range(n):
        day = random.randint(1, 28)
        date_str = f"2024/01/{day:02d}"
        cat = random.choice(categories)
        item_name, unit_cost, typical_stock = random.choice(items_by_cat[cat])
        item_code = f"ITM-{abs(hash(item_name)) % 9000 + 1000}"
        min_stock = int(typical_stock * random.uniform(0.2, 0.4))
        # 在庫数量：10%の確率で欠品状態（min_stock 未満）を作る
        if random.random() < 0.10:
            stock_qty = random.randint(0, max(0, min_stock - 1))
        else:
            stock_qty = int(typical_stock * random.uniform(0.5, 1.5))
        received_qty = random.randint(0, int(typical_stock * 0.3))
        shipped_qty = random.randint(0, min(stock_qty, int(typical_stock * 0.2)))

        if col_style == "standard":
            rows.append({
                "日付": date_str, "倉庫名": warehouse_name,
                "品目コード": item_code, "品目名": item_name, "カテゴリ": cat,
                "在庫数量": stock_qty, "最低在庫数": min_stock,
                "単価": unit_cost, "入庫数量": received_qty, "出庫数量": shipped_qty,
            })
        elif col_style == "english":
            rows.append({
                "Date": date_str, "Warehouse": warehouse_name,
                "ItemCode": item_code, "ItemName": item_name, "Category": cat,
                "StockQty": stock_qty, "MinStock": min_stock,
                "UnitCost": unit_cost, "ReceivedQty": received_qty, "ShippedQty": shipped_qty,
            })
        elif col_style == "variant":
            rows.append({
                "集計日": date_str, "倉庫": warehouse_name,
                "コード": item_code, "品名": item_name, "分類": cat,
                "在庫": stock_qty, "安全在庫": min_stock,
                "原価": unit_cost, "入庫": received_qty, "出庫": shipped_qty,
            })
    return rows


warehouses = [
    ("東京第1倉庫", "standard", "01_東京第1倉庫_在庫_202401.csv"),
    ("大阪第2倉庫", "english",  "02_大阪第2倉庫_在庫_202401.csv"),
    ("名古屋倉庫",  "variant",  "03_名古屋倉庫_在庫_202401.csv"),
    ("福岡倉庫",    "standard", "04_福岡倉庫_在庫_202401.csv"),
    ("札幌倉庫",    "standard", "05_札幌倉庫_在庫_202401.csv"),
]

for warehouse_name, style, filename in warehouses:
    n = random.randint(110, 160)
    rows = gen_rows(warehouse_name, n=n, col_style=style)
    df = pd.DataFrame(rows)
    df.to_csv(out / filename, index=False, encoding="utf-8-sig")
    print(f"Created {filename}: {len(df)} rows, style={style}")

print("\nサンプルデータ生成完了（5倉庫）")
```

---

- [ ] **Step 1-7: `_gen_sample_data.py` を実行してサンプルデータを生成する**

```
C:\Users\realp\miniconda3\python.exe "C:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\05_logistics\01_inventory\_gen_sample_data.py"
```

期待出力:
```
Created 01_東京第1倉庫_在庫_202401.csv: XXX rows, style=standard
Created 02_大阪第2倉庫_在庫_202401.csv: XXX rows, style=english
Created 03_名古屋倉庫_在庫_202401.csv: XXX rows, style=variant
Created 04_福岡倉庫_在庫_202401.csv: XXX rows, style=standard
Created 05_札幌倉庫_在庫_202401.csv: XXX rows, style=standard
サンプルデータ生成完了（5倉庫）
```

5つのCSVが `05_logistics/01_inventory/` 直下に生成されることを確認する。

---

- [ ] **Step 1-8: `.claude/agents/inventory-cleaner.md` を作成する**

`C:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\05_logistics\01_inventory\.claude\agents\inventory-cleaner.md` に書き込む:

```markdown
---
name: inventory-cleaner
description: 物流倉庫在庫データのクレンジング専門エージェント。カレントディレクトリの .csv ファイルを読み込み、列名統一・日付フォーマット統一・数値補完を行い output/cleaned_inventory_202401.csv に出力する。全18項目のバリデーションが全PASS するまで自律的に PDCA ループで修正を繰り返す。「クレンジングして」「データを整形して」「inventory-cleaner」と言われたときに使用する。
tools:
  - Read
  - Write
  - Bash
---

あなたはデータクレンジングの専門家です。以下の手順で在庫データを処理し、全18項目のチェックが PASS するまで自律的に修正を繰り返してください。

## 処理手順

### Step 1: 必要なライブラリの確認

```bash
C:\Users\realp\miniconda3\python.exe -c "import pandas; print('OK')"
```

エラーが出た場合は `C:\Users\realp\miniconda3\python.exe -m pip install pandas` を実行する。

### Step 2: output ディレクトリを作成する

```bash
C:\Users\realp\miniconda3\python.exe -c "import pathlib; pathlib.Path('output').mkdir(exist_ok=True); print('output/ OK')"
```

### Step 3: クレンジングスクリプトを output/cleanse.py に書く

Write ツールで以下の内容を output/cleanse.py に書き込む:

```python
"""
物流倉庫在庫データクレンジングスクリプト
5倉庫分のバラバラな CSV を統一フォーマットに整形する
"""
import pandas as pd
import re
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    # date
    "日付": "date", "Date": "date", "集計日": "date",
    # warehouse
    "倉庫名": "warehouse", "Warehouse": "warehouse", "倉庫": "warehouse",
    # item_code
    "品目コード": "item_code", "ItemCode": "item_code", "コード": "item_code",
    # item_name
    "品目名": "item_name", "ItemName": "item_name", "品名": "item_name",
    # category
    "カテゴリ": "category", "Category": "category", "分類": "category",
    # stock_qty
    "在庫数量": "stock_qty", "StockQty": "stock_qty", "在庫": "stock_qty",
    # min_stock_qty
    "最低在庫数": "min_stock_qty", "MinStock": "min_stock_qty", "安全在庫": "min_stock_qty",
    # unit_cost
    "単価": "unit_cost", "UnitCost": "unit_cost", "原価": "unit_cost",
    # received_qty
    "入庫数量": "received_qty", "ReceivedQty": "received_qty", "入庫": "received_qty",
    # shipped_qty
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

### Step 4: バリデーションスクリプトを output/validate.py に書く

Write ツールで以下の内容を output/validate.py に書き込む:

```python
"""
在庫データ品質チェックリスト（18項目）- 物流 A-03 版
"""
import json
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

import re

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

### Step 5: PDCA ループ（最大5ラウンド）

以下のサイクルを最大5ラウンド繰り返す（カレントディレクトリを `05_logistics/01_inventory/` にして実行）。

1. `C:\Users\realp\miniconda3\python.exe output/cleanse.py` を実行する
2. `C:\Users\realp\miniconda3\python.exe output/validate.py` を実行する
3. `output/result.json` を Read ツールで読み込む
4. `"all_passed"` が `true` → Step 6 へ進む
5. `"all_passed"` が `false` の場合: `"status": "FAIL"` の項目の `fix_hint` を読み、`output/cleanse.py` の該当箇所を修正する

5ラウンド後も失敗が残る場合: STOP を出力して終了する

### Step 6: 完了レポートを出力する

```
クレンジング完了（PDCA Round {N}）
行数: {総行数}  倉庫数: {倉庫数}  全18項目 PASS
```

## 重要な注意事項

- python コマンドは `C:\Users\realp\miniconda3\python.exe` を使うこと
- validate.py 自体は PDCA ループ中に修正しない
- カレントディレクトリは `05_logistics/01_inventory/` であること（CSVがそこにある）
```

---

- [ ] **Step 1-9: `.claude/agents/data-analyst.md` を作成する**

`C:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\05_logistics\01_inventory\.claude\agents\data-analyst.md` に書き込む:

```markdown
---
name: data-analyst
description: 物流倉庫在庫分析・欠品検知専門エージェント。output/cleaned_inventory_202401.csv を読み込み、倉庫別在庫サマリー・欠品検知・在庫回転率・異常値検出をまとめた output/analysis_report.md を生成する。全7項目のレポート品質チェックが全PASS するまで自律的に PDCA ループで修正を繰り返す。「分析して」「欠品を検知して」「data-analyst」と言われたときに使用する。前提: inventory-cleaner を先に実行済みであること。
tools:
  - Read
  - Write
  - Bash
---

あなたは在庫分析の専門家です。以下の手順で在庫データを分析し、全7項目のレポート品質チェックが PASS するまで自律的に修正を繰り返してください。

## Step 1: 前提確認

```bash
C:\Users\realp\miniconda3\python.exe -c "from pathlib import Path; assert Path('output/cleaned_inventory_202401.csv').exists(), 'ERROR: inventory-cleaner を先に実行してください'; print('OK')"
```

## Step 2: 分析スクリプトを output/analyze.py に書く

Write ツールで以下の内容を output/analyze.py に書き込む:

```python
import pandas as pd
import numpy as np
from pathlib import Path

STOCKOUT_THRESHOLD = 0          # stock_qty < min_stock_qty → 欠品
LOW_STOCK_RATIO_THRESHOLD = 0.20  # 欠品率20%超でアラート

df = pd.read_csv("output/cleaned_inventory_202401.csv", encoding="utf-8-sig")

for col in ["stock_qty", "min_stock_qty", "unit_cost", "received_qty", "shipped_qty"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

# 欠品フラグ: stock_qty < min_stock_qty
df["stockout_flag"] = df["stock_qty"] < df["min_stock_qty"]

# 在庫金額
df["stock_value"] = df["stock_qty"] * df["unit_cost"]

# 在庫回転率（0除算防止）
df["turnover_rate"] = df.apply(
    lambda r: r["shipped_qty"] / r["stock_qty"] if r["stock_qty"] > 0 else 0.0,
    axis=1,
)

lines = ["# 在庫データ分析レポート（2024年1月）\n"]

# 1. 倉庫別在庫サマリー
lines.append("## 1. 倉庫別在庫サマリー\n")
wh_summary = df.groupby("warehouse").agg(
    在庫金額合計=("stock_value", "sum"),
    平均在庫数=("stock_qty", "mean"),
    品目数=("item_code", "nunique"),
).sort_values("在庫金額合計", ascending=False)
wh_fmt = wh_summary.copy()
wh_fmt["在庫金額合計"] = wh_fmt["在庫金額合計"].map("{:,.0f}円".format)
wh_fmt["平均在庫数"] = wh_fmt["平均在庫数"].map("{:.1f}".format)
lines.append(wh_fmt.to_markdown())
lines.append("")

# 2. 欠品検知
lines.append("## 2. 欠品検知\n")
stockout_df = df[df["stockout_flag"]].copy()
total_items = len(df)
stockout_count = int(df["stockout_flag"].sum())
stockout_ratio = stockout_count / total_items * 100 if total_items > 0 else 0

lines.append(f"- 欠品品目数: **{stockout_count}件** / {total_items}件 ({stockout_ratio:.1f}%)")
if stockout_ratio > LOW_STOCK_RATIO_THRESHOLD * 100:
    lines.append(f"- **アラート: 欠品率 {stockout_ratio:.1f}% が閾値 {LOW_STOCK_RATIO_THRESHOLD*100:.0f}% を超過**")
else:
    lines.append(f"- 欠品率 {stockout_ratio:.1f}% は閾値（{LOW_STOCK_RATIO_THRESHOLD*100:.0f}%）以内で正常範囲です")
lines.append("")

if stockout_count > 0:
    lines.append("### 欠品品目一覧（在庫数量 < 最低在庫数）\n")
    show_cols = [c for c in ["warehouse", "item_code", "item_name", "category",
                              "stock_qty", "min_stock_qty"] if c in stockout_df.columns]
    lines.append(stockout_df[show_cols].to_markdown(index=False))
    lines.append("")

# 3. 倉庫別欠品品目数
lines.append("## 3. 倉庫別欠品品目数\n")
stockout_by_wh = df.groupby("warehouse")["stockout_flag"].sum().sort_values(ascending=False)
for wh, cnt in stockout_by_wh.items():
    lines.append(f"- {wh}: {int(cnt)}件")
lines.append("")

# 4. 在庫回転率分析
lines.append("## 4. 在庫回転率分析\n")
turnover_summary = df.groupby("category")["turnover_rate"].agg(
    平均回転率="mean",
    最大回転率="max",
    最小回転率="min",
).sort_values("平均回転率", ascending=False)
lines.append(turnover_summary.round(3).to_markdown())
lines.append("")

# 5. 異常値検出（倉庫×日次在庫金額 ±2σ）
lines.append("## 5. 異常値検出（±2σ）\n")
anomalies = []
if "date" in df.columns:
    daily_value = df.groupby(["warehouse", "date"])["stock_value"].sum().reset_index()
    for wh, grp in daily_value.groupby("warehouse"):
        if len(grp) > 2:
            mean = grp["stock_value"].mean()
            std = grp["stock_value"].std()
            if std > 0:
                outliers = grp[np.abs(grp["stock_value"] - mean) > 2 * std]
                for _, row in outliers.iterrows():
                    date_str = str(row["date"])[:10]
                    anomalies.append(
                        f"- {wh} | {date_str} | {row['stock_value']:,.0f}円"
                        f"（平均 {mean:,.0f}円 から {(row['stock_value']-mean)/std:+.1f}σ）"
                    )
if anomalies:
    lines.extend(anomalies)
else:
    lines.append("- 異常値は検出されませんでした")
lines.append("")

# 6. ビジネスインサイト
lines.append("## 6. ビジネスインサイト\n")
total_stock_value = df["stock_value"].sum()
wh_totals = df.groupby("warehouse")["stock_value"].sum()
top_wh = wh_totals.idxmax()
bottom_wh = wh_totals.idxmin()
lines.append(f"- 総在庫金額: **{total_stock_value:,.0f}円**")
lines.append(f"- 在庫金額最大倉庫: **{top_wh}**（{wh_totals[top_wh]:,.0f}円）")
lines.append(f"- 在庫金額最小倉庫: **{bottom_wh}**（{wh_totals[bottom_wh]:,.0f}円）")
if stockout_count > 0:
    lines.append(f"- 欠品品目 {stockout_count} 件が検出されました — 緊急発注を検討してください")
if anomalies:
    lines.append(f"- 在庫金額の異常値が {len(anomalies)} 件検出されました — 要因調査を推奨")
lines.append("")

Path("output/analysis_report.md").write_text("\n".join(lines), encoding="utf-8")
print("分析完了: output/analysis_report.md を生成しました")
```

## Step 3: レポート品質チェックスクリプトを output/validate_report.py に書く

Write ツールで以下の内容を output/validate_report.py に書き込む:

```python
"""
レポート品質チェックリスト（7項目）- 物流 A-03 版
"""
import json
import re
from pathlib import Path

REPORT_PATH = Path("output/analysis_report.md")
CSV_PATH = Path("output/cleaned_inventory_202401.csv")
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

    sections = ["倉庫別在庫サマリー", "欠品検知", "倉庫別欠品品目数",
                "在庫回転率", "異常値検出", "ビジネスインサイト"]
    missing_sec = [s for s in sections if s not in text]
    check(2, "all_sections_present", len(missing_sec) == 0,
          f"欠落セクション: {missing_sec}",
          "analyze.py の各分析ブロック（## N. セクション名）を確認する")

    if CSV_PATH.exists():
        import pandas as pd
        df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
        warehouses = df["warehouse"].unique().tolist() if "warehouse" in df.columns else []
        missing_wh = [w for w in warehouses if w not in text]
        check(3, "all_warehouses_in_report", len(missing_wh) == 0,
              f"レポートに未掲載の倉庫: {missing_wh}",
              "wh_summary / groupby('warehouse') を確認")
    else:
        check(3, "all_warehouses_in_report", False,
              "cleaned_inventory_202401.csv が存在しない",
              "inventory-cleaner を先に実行する")

    keywords = ["欠品品目数", "総在庫金額", "在庫金額"]
    missing_kw = [k for k in keywords if k not in text]
    check(4, "insight_keywords", len(missing_kw) == 0,
          f"インサイトセクションに欠落キーワード: {missing_kw}",
          "analyze.py の '6. ビジネスインサイト' セクションを確認")

    anomaly_match = re.search(r"## 5.*?(?=## 6|\Z)", text, re.DOTALL)
    anomaly_lines = len(anomaly_match.group(0).strip().splitlines()) if anomaly_match else 0
    check(5, "anomaly_section_content", anomaly_lines >= 2,
          f"異常値検出セクションが薄い（{anomaly_lines}行）",
          "analyze.py の ±2σ 異常値検出ロジックを確認")

    has_numbers = bool(re.search(r"\d{1,3}(,\d{3})+円", text))
    check(6, "numeric_values_present", has_numbers,
          "レポートに金額（例: 1,234,567円）が含まれない",
          "analyze.py の format 処理（{:,.0f}円）を確認")

    stockout_section_ok = "欠品" in text and "%" in text
    check(7, "stockout_section", stockout_section_ok,
          "欠品検知セクションが存在しないか内容が空",
          "analyze.py の '2. 欠品検知' セクションを確認")

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

3ラウンド後も失敗が残る場合: STOP を出力して終了する

## Step 5: 完了レポートを出力する

```
分析完了（PDCA Round {N}）
全7項目 PASS → output/analysis_report.md を確認してください
```

## 重要な注意事項

- python コマンドは `C:\Users\realp\miniconda3\python.exe` を使うこと
- validate_report.py 自体は PDCA ループ中に修正しない
- カレントディレクトリは `05_logistics/01_inventory/` であること
```

---

- [ ] **Step 1-10: git commit する**

```bash
git add dx-portfolio/05_logistics/
git commit -m "feat(A-03): add directory structure, config, agents, sample data"
```

---

## Task 2: クレンジング PDCA

**Files:**
- Generate/run: `05_logistics/01_inventory/output/cleanse.py`
- Generate/run: `05_logistics/01_inventory/output/validate.py`
- Output: `05_logistics/01_inventory/output/cleaned_inventory_202401.csv`
- Output: `05_logistics/01_inventory/output/result.json`

実行はすべて `05_logistics/01_inventory/` をカレントディレクトリとして行うこと。

---

- [ ] **Step 2-1: inventory-cleaner エージェントを起動して cleanse.py を生成・実行する**

`inventory-cleaner` エージェントを使用する（Task 1 Step 1-8 で作成した `.claude/agents/inventory-cleaner.md` の手順を実行する）。

エージェントが実行する内容:
1. `output/cleanse.py` を書く
2. `output/validate.py` を書く
3. `C:\Users\realp\miniconda3\python.exe output/cleanse.py` を実行
4. `C:\Users\realp\miniconda3\python.exe output/validate.py` を実行
5. `output/result.json` を確認して全18項目 PASS まで PDCA

エージェントを使わず手動で実行する場合は、Task 1 Step 1-8 の inventory-cleaner.md に埋め込まれた cleanse.py / validate.py の全コードを `output/` ディレクトリに書き込んでから実行する。

- [ ] **Step 2-2: 全18項目 PASS を確認する**

```
C:\Users\realp\miniconda3\python.exe -c "
import json
from pathlib import Path
r = json.loads(Path('output/result.json').read_text(encoding='utf-8'))
print('passed:', r['passed'], '/ failed:', r['failed'])
assert r['all_passed'], 'FAIL items: ' + str([x for x in r['results'] if x['status']=='FAIL'])
print('全18項目 PASS')
"
```

期待出力: `全18項目 PASS`

- [ ] **Step 2-3: git commit する**

```bash
git add dx-portfolio/05_logistics/01_inventory/output/cleanse.py dx-portfolio/05_logistics/01_inventory/output/validate.py dx-portfolio/05_logistics/01_inventory/output/cleaned_inventory_202401.csv dx-portfolio/05_logistics/01_inventory/output/result.json dx-portfolio/05_logistics/01_inventory/output/cleansing_log.md
git commit -m "feat(A-03): add cleanse.py + validate.py, all 18 checks PASS"
```

---

## Task 3: 分析 PDCA

**Files:**
- Generate/run: `05_logistics/01_inventory/output/analyze.py`
- Generate/run: `05_logistics/01_inventory/output/validate_report.py`
- Output: `05_logistics/01_inventory/output/analysis_report.md`
- Output: `05_logistics/01_inventory/output/result_analysis.json`

---

- [ ] **Step 3-1: data-analyst エージェントを起動して analyze.py を生成・実行する**

`data-analyst` エージェントを使用する（Task 1 Step 1-9 で作成した `.claude/agents/data-analyst.md` の手順を実行する）。

エージェントが実行する内容:
1. `output/analyze.py` を書く
2. `output/validate_report.py` を書く
3. `C:\Users\realp\miniconda3\python.exe output/analyze.py` を実行
4. `C:\Users\realp\miniconda3\python.exe output/validate_report.py` を実行
5. `output/result_analysis.json` を確認して全7項目 PASS まで PDCA

- [ ] **Step 3-2: 全7項目 PASS を確認する**

```
C:\Users\realp\miniconda3\python.exe -c "
import json
from pathlib import Path
r = json.loads(Path('output/result_analysis.json').read_text(encoding='utf-8'))
print('passed:', r['passed'], '/ failed:', r['failed'])
assert r['all_passed'], 'FAIL items: ' + str([x for x in r['results'] if x['status']=='FAIL'])
print('全7項目 PASS')
"
```

期待出力: `全7項目 PASS`

- [ ] **Step 3-3: git commit する**

```bash
git add dx-portfolio/05_logistics/01_inventory/output/analyze.py dx-portfolio/05_logistics/01_inventory/output/validate_report.py dx-portfolio/05_logistics/01_inventory/output/analysis_report.md dx-portfolio/05_logistics/01_inventory/output/result_analysis.json
git commit -m "feat(A-03): add analyze.py + validate_report.py, all 7 checks PASS"
```

---

## Task 4: 可視化

**Files:**
- Create: `05_logistics/01_inventory/.claude/agents/data-viz-engineer.md`
- Generate/run: `05_logistics/01_inventory/output/visualize.py`
- Output: `05_logistics/01_inventory/output/charts/bar_warehouse_stock.png`
- Output: `05_logistics/01_inventory/output/charts/bar_stockout_items.png`
- Output: `05_logistics/01_inventory/output/charts/scatter_turnover.png`

---

- [ ] **Step 4-1: `data-viz-engineer.md` を作成する**

`C:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\05_logistics\01_inventory\.claude\agents\data-viz-engineer.md` に書き込む:

```markdown
---
name: data-viz-engineer
description: 物流倉庫在庫・欠品検知可視化専門エージェント。output/cleaned_inventory_202401.csv を読み込み、倉庫別在庫金額棒グラフ・倉庫別欠品品目数棒グラフ（赤棒）・品目別在庫回転率散布図を output/charts/ に出力する。「グラフを作って」「可視化して」「data-viz-engineer」と言われたときに使用する。前提: data-analyst を先に実行済みであること。
tools:
  - Read
  - Write
  - Bash
---

あなたはデータ可視化の専門家です。以下の手順でグラフを生成してください。

## Step 1: 前提確認

```bash
C:\Users\realp\miniconda3\python.exe -c "from pathlib import Path; assert Path('output/cleaned_inventory_202401.csv').exists(); print('OK')"
```

## Step 2: output/charts ディレクトリを作成する

```bash
C:\Users\realp\miniconda3\python.exe -c "import pathlib; pathlib.Path('output/charts').mkdir(parents=True, exist_ok=True); print('charts/ OK')"
```

## Step 3: visualize.py を output/visualize.py に書く

Write ツールで以下の内容を output/visualize.py に書き込む:

```python
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import japanize_matplotlib
import numpy as np
from pathlib import Path

df = pd.read_csv("output/cleaned_inventory_202401.csv", encoding="utf-8-sig")
for col in ["stock_qty", "min_stock_qty", "unit_cost", "received_qty", "shipped_qty"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

df["stock_value"] = df["stock_qty"] * df["unit_cost"]
df["stockout_flag"] = df["stock_qty"] < df["min_stock_qty"]
df["turnover_rate"] = df.apply(
    lambda r: r["shipped_qty"] / r["stock_qty"] if r["stock_qty"] > 0 else 0.0, axis=1
)

charts_dir = Path("output/charts")
charts_dir.mkdir(parents=True, exist_ok=True)

# 1. 倉庫別在庫金額棒グラフ
wh_stock = df.groupby("warehouse")["stock_value"].sum().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(wh_stock.index, wh_stock.values, color="#2563eb")
ax.set_title("倉庫別在庫金額（2024年1月）", fontsize=14)
ax.set_ylabel("在庫金額（円）")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
for bar in bars:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h + h*0.01,
            f"{h:,.0f}", ha="center", va="bottom", fontsize=9)
plt.tight_layout()
plt.savefig(charts_dir / "bar_warehouse_stock.png", dpi=150)
plt.close()
print("Saved: bar_warehouse_stock.png")

# 2. 倉庫別欠品品目数棒グラフ（赤棒）
stockout_by_wh = df.groupby("warehouse")["stockout_flag"].sum().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(stockout_by_wh.index, stockout_by_wh.values, color="#ef4444")
ax.set_title("倉庫別欠品品目数（2024年1月）", fontsize=14)
ax.set_ylabel("欠品品目数（件）")
for bar, v in zip(bars, stockout_by_wh.values):
    ax.text(bar.get_x() + bar.get_width()/2, v + 0.1,
            str(int(v)), ha="center", va="bottom", fontsize=10)
plt.tight_layout()
plt.savefig(charts_dir / "bar_stockout_items.png", dpi=150)
plt.close()
print("Saved: bar_stockout_items.png")

# 3. 品目別在庫回転率散布図（欠品品目は赤点）
item_stats = df.groupby("item_name").agg(
    turnover=("turnover_rate", "mean"),
    stockout=("stockout_flag", "any"),
    stock_value=("stock_value", "sum"),
).reset_index()
colors = ["#ef4444" if s else "#2563eb" for s in item_stats["stockout"]]
fig, ax = plt.subplots(figsize=(12, 6))
ax.scatter(
    range(len(item_stats)),
    item_stats["turnover"],
    c=colors, alpha=0.7, s=60,
)
ax.set_title("品目別在庫回転率（赤=欠品品目）（2024年1月）", fontsize=14)
ax.set_ylabel("在庫回転率（shipped / stock）")
ax.set_xlabel("品目インデックス")
# 凡例
from matplotlib.patches import Patch
ax.legend(handles=[
    Patch(color="#ef4444", label="欠品品目"),
    Patch(color="#2563eb", label="正常品目"),
])
plt.tight_layout()
plt.savefig(charts_dir / "scatter_turnover.png", dpi=150)
plt.close()
print("Saved: scatter_turnover.png")

print("グラフ生成完了")
```

## Step 4: visualize.py を実行する

```bash
C:\Users\realp\miniconda3\python.exe output/visualize.py
```

期待出力:
```
Saved: bar_warehouse_stock.png
Saved: bar_stockout_items.png
Saved: scatter_turnover.png
グラフ生成完了
```

japanize_matplotlib がない場合は先に `C:\Users\realp\miniconda3\python.exe -m pip install japanize-matplotlib` を実行する。

## Step 5: ファイル存在と10KB超を確認する

```bash
C:\Users\realp\miniconda3\python.exe -c "
from pathlib import Path
for p in [
    'output/charts/bar_warehouse_stock.png',
    'output/charts/bar_stockout_items.png',
    'output/charts/scatter_turnover.png',
]:
    size = Path(p).stat().st_size if Path(p).exists() else 0
    status = 'OK' if size > 10_000 else ('EXISTS but tiny' if size > 0 else 'MISSING')
    print(f'{p}: {status} ({size:,} bytes)')"
```

期待出力: 各ファイルに `OK` と表示される（10KB 超）

## 重要な注意事項

- python コマンドは `C:\Users\realp\miniconda3\python.exe` を使うこと
- カレントディレクトリは `05_logistics/01_inventory/` であること
```

---

- [ ] **Step 4-2: data-viz-engineer エージェントを起動して visualize.py を生成・実行する**

`data-viz-engineer` エージェントを使用する（Step 4-1 で作成した `.claude/agents/data-viz-engineer.md` の手順を実行する）。

- [ ] **Step 4-3: 3つの PNG ファイルが 10KB 超であることを確認する**

```
C:\Users\realp\miniconda3\python.exe -c "
from pathlib import Path
charts = Path('output/charts')
for name in ['bar_warehouse_stock.png', 'bar_stockout_items.png', 'scatter_turnover.png']:
    p = charts / name
    assert p.exists() and p.stat().st_size > 10_000, f'FAIL: {name}'
    print(f'OK: {name} ({p.stat().st_size:,} bytes)')
print('全3グラフ確認完了')
"
```

期待出力: `全3グラフ確認完了`

- [ ] **Step 4-4: git commit する**

```bash
git add "dx-portfolio/05_logistics/01_inventory/.claude/agents/data-viz-engineer.md" dx-portfolio/05_logistics/01_inventory/output/visualize.py dx-portfolio/05_logistics/01_inventory/output/charts/
git commit -m "feat(A-03): add data-viz-engineer agent and 3 PNG charts"
```

---

## Task 5: Streamlit app.py

**Files:**
- Create: `05_logistics/01_inventory/app.py`

---

- [ ] **Step 5-1: `app.py` を作成する**

`C:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\05_logistics\01_inventory\app.py` に書き込む:

```python
import streamlit as st
import pandas as pd
import yaml
from pathlib import Path

st.set_page_config(
    page_title="物流 在庫・欠品検知ダッシュボード",
    page_icon="📦",
    layout="wide",
)

BASE = Path(__file__).parent

with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

STOCKOUT_THRESHOLD = config.get("stockout_alert_threshold", 0)
LOW_STOCK_RATIO_THRESHOLD = config.get("low_stock_ratio_threshold", 0.20)


@st.cache_data
def load_data():
    df = pd.read_csv(BASE / "output" / "cleaned_inventory_202401.csv", encoding="utf-8-sig")
    for col in ["stock_qty", "min_stock_qty", "unit_cost", "received_qty", "shipped_qty"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["stock_value"] = df["stock_qty"] * df["unit_cost"]
    df["stockout_flag"] = df["stock_qty"] < df["min_stock_qty"]
    return df


@st.cache_data
def load_report():
    p = BASE / "output" / "analysis_report.md"
    return p.read_text(encoding="utf-8") if p.exists() else "レポートが見つかりません"


df_all = load_data()
report_text = load_report()

st.title("📦 物流 在庫・欠品検知ダッシュボード")
st.caption("2024年1月 | 5倉庫")

# 倉庫フィルター
warehouses = sorted(df_all["warehouse"].dropna().unique().tolist())
selected = st.multiselect("倉庫フィルター", warehouses, default=warehouses)
df = df_all[df_all["warehouse"].isin(selected)] if selected else df_all

# メトリクスカード
total_stock_value = df["stock_value"].sum()
stockout_count = int(df["stockout_flag"].sum())
total_items = len(df)
stockout_ratio = stockout_count / total_items * 100 if total_items > 0 else 0
warehouse_count = df["warehouse"].nunique()
row_count = len(df)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("総在庫金額", f"¥{total_stock_value:,.0f}")
alert_color = "inverse" if stockout_count > 0 else "normal"
c2.metric("欠品品目数", f"{stockout_count} 件",
          delta="要対応" if stockout_count > 0 else "正常",
          delta_color=alert_color)
ratio_delta = f"{'⚠ アラート' if stockout_ratio > LOW_STOCK_RATIO_THRESHOLD * 100 else '正常'}"
c3.metric("欠品率", f"{stockout_ratio:.1f}%", delta=ratio_delta,
          delta_color="inverse" if stockout_ratio > LOW_STOCK_RATIO_THRESHOLD * 100 else "normal")
c4.metric("対象倉庫数", f"{warehouse_count} 倉庫")
c5.metric("レコード数", f"{row_count:,} 件")

st.divider()

# グラフタブ
tab1, tab2, tab3 = st.tabs(["📊 倉庫別在庫金額", "🔴 倉庫別欠品品目数", "📈 在庫回転率"])

charts_dir = BASE / "output" / "charts"

with tab1:
    p = charts_dir / "bar_warehouse_stock.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning("グラフが見つかりません。run_pipeline.py を実行してください。")

with tab2:
    p = charts_dir / "bar_stockout_items.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
        st.caption("赤棒 = 欠品品目数（stock_qty < min_stock_qty）")
    else:
        st.warning("グラフが見つかりません。run_pipeline.py を実行してください。")

with tab3:
    p = charts_dir / "scatter_turnover.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
        st.caption("赤点 = 欠品品目、青点 = 正常品目")
    else:
        st.warning("グラフが見つかりません。run_pipeline.py を実行してください。")

st.divider()

# 欠品品目テーブル
st.subheader("欠品品目一覧")
stockout_items = df[df["stockout_flag"]].copy()
if len(stockout_items) > 0:
    show_cols = [c for c in ["warehouse", "item_code", "item_name", "category",
                              "stock_qty", "min_stock_qty", "unit_cost"] if c in stockout_items.columns]
    st.dataframe(stockout_items[show_cols].sort_values("warehouse"), use_container_width=True)
else:
    st.success("欠品品目はありません")

st.divider()

# 倉庫別在庫サマリーテーブル
st.subheader("倉庫別在庫サマリー")
wh_tbl = df.groupby("warehouse").agg(
    在庫金額合計=("stock_value", "sum"),
    欠品品目数=("stockout_flag", "sum"),
    品目数=("item_code", "nunique"),
).copy()
wh_tbl["欠品率(%)"] = (wh_tbl["欠品品目数"] / df.groupby("warehouse").size() * 100).round(1)
wh_tbl["アラート"] = wh_tbl["欠品品目数"].apply(
    lambda x: "⚠ 要対応" if x > 0 else "✅ 正常"
)
wh_tbl["在庫金額合計"] = wh_tbl["在庫金額合計"].apply(lambda x: f"¥{x:,.0f}")
wh_tbl = wh_tbl.sort_values("欠品品目数", ascending=False)
st.dataframe(wh_tbl, use_container_width=True)

st.divider()

# 分析レポート
with st.expander("📋 分析レポートを見る", expanded=False):
    st.markdown(report_text)
```

- [ ] **Step 5-2: 構文チェックを実行する**

```
C:\Users\realp\miniconda3\python.exe -m py_compile "C:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\05_logistics\01_inventory\app.py" && echo "構文OK"
```

期待出力: `構文OK`

- [ ] **Step 5-3: git commit する**

```bash
git add dx-portfolio/05_logistics/01_inventory/app.py
git commit -m "feat(A-03): add Streamlit dashboard app.py with stockout metrics"
```

---

## Task 6: pytest テスト

**Files:**
- Create: `05_logistics/01_inventory/tests/__init__.py`
- Create: `05_logistics/01_inventory/tests/test_cleaner_output.py`
- Create: `05_logistics/01_inventory/tests/test_analyst_output.py`
- Create: `05_logistics/01_inventory/tests/test_viz_output.py`

pytest は `05_logistics/01_inventory/` をカレントディレクトリとして実行する。

---

- [ ] **Step 6-1: `tests/__init__.py` を作成する**

`C:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\05_logistics\01_inventory\tests\__init__.py` に空ファイルを作成する:

```
C:\Users\realp\miniconda3\python.exe -c "from pathlib import Path; Path('C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/05_logistics/01_inventory/tests/__init__.py').touch(); print('OK')"
```

- [ ] **Step 6-2: `tests/test_cleaner_output.py` を作成する（14テスト）**

`C:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\05_logistics\01_inventory\tests\test_cleaner_output.py` に書き込む:

```python
import pandas as pd
import pytest
from pathlib import Path

CSV = Path("output/cleaned_inventory_202401.csv")


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(CSV, encoding="utf-8-sig")


def test_csv_exists():
    assert CSV.exists()


def test_row_count(df):
    assert 400 <= len(df) <= 1000


def test_required_columns(df):
    required = {
        "date", "warehouse", "item_code", "item_name", "category",
        "stock_qty", "min_stock_qty", "unit_cost",
        "received_qty", "shipped_qty", "source_file",
    }
    assert required.issubset(set(df.columns))


def test_warehouse_count(df):
    assert df["warehouse"].nunique() == 5


def test_no_null_date(df):
    assert df["date"].notna().all()


def test_no_null_warehouse(df):
    assert df["warehouse"].notna().all()


def test_stock_qty_nonneg(df):
    assert (df["stock_qty"] >= 0).all()


def test_min_stock_qty_nonneg(df):
    assert (df["min_stock_qty"] >= 0).all()


def test_unit_cost_nonneg(df):
    assert (df["unit_cost"] >= 0).all()


def test_received_qty_nonneg(df):
    assert (df["received_qty"] >= 0).all()


def test_shipped_qty_nonneg(df):
    assert (df["shipped_qty"] >= 0).all()


def test_expected_warehouses(df):
    warehouses = set(df["warehouse"].unique())
    assert "東京第1倉庫" in warehouses


def test_col_order(df):
    first_cols = list(df.columns[:3])
    assert first_cols == ["date", "warehouse", "item_code"]


def test_source_file_nonempty(df):
    assert df["source_file"].notna().all()
```

- [ ] **Step 6-3: `tests/test_analyst_output.py` を作成する（6テスト）**

`C:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\05_logistics\01_inventory\tests\test_analyst_output.py` に書き込む:

```python
import pytest
from pathlib import Path

REPORT = Path("output/analysis_report.md")


@pytest.fixture(scope="module")
def report():
    return REPORT.read_text(encoding="utf-8")


def test_report_exists():
    assert REPORT.exists()


def test_report_has_warehouse_section(report):
    assert "倉庫" in report


def test_report_has_stockout_section(report):
    assert "欠品" in report


def test_report_has_turnover_section(report):
    assert "回転率" in report


def test_report_has_alert_marker(report):
    assert "%" in report


def test_report_has_anomaly_section(report):
    assert "異常" in report or "検出" in report
```

- [ ] **Step 6-4: `tests/test_viz_output.py` を作成する（4テスト）**

`C:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\05_logistics\01_inventory\tests\test_viz_output.py` に書き込む:

```python
import pytest
from pathlib import Path

CHARTS = Path("output/charts")


def test_charts_dir_exists():
    assert CHARTS.exists()


def test_bar_warehouse_stock_exists():
    assert (CHARTS / "bar_warehouse_stock.png").exists()


def test_bar_stockout_items_exists():
    assert (CHARTS / "bar_stockout_items.png").exists()


def test_scatter_turnover_exists():
    assert (CHARTS / "scatter_turnover.png").exists()
```

- [ ] **Step 6-5: 全24テストを実行して PASS を確認する**

```
C:\Users\realp\miniconda3\python.exe -m pytest tests/ -v
```

期待出力（最終行）:
```
24 passed in X.XXs
```

全24テストが PASS すること。FAIL があった場合は対応する output/ ファイルを確認して修正する。

- [ ] **Step 6-6: git commit する**

```bash
git add dx-portfolio/05_logistics/01_inventory/tests/
git commit -m "feat(A-03): add 24 pytest tests, all passing"
```

---

## Task 7: catalog.yml 更新・STATUS.md 更新

**Files:**
- Modify: `dx-portfolio/catalog.yml` — A-03 エントリを `production-ready` に更新
- Modify: `05_logistics/01_inventory/STATUS.md` — status を `production-ready` に更新

---

- [ ] **Step 7-1: `catalog.yml` の A-03 エントリを更新する**

`c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\catalog.yml` の A-03 エントリを以下のように変更する（既存の `status: "idea"` / `path: null` / `demo: null` を書き換える）:

```yaml
- id: "A-03"
  name: "在庫データクレンジング・欠品検知"
  industry: "物流・倉庫"
  department: "物流・在庫"
  status: "production-ready"
  priority: "A"
  path: "05_logistics/01_inventory"
  description: "複数倉庫の在庫データを統合クレンジングし、欠品リスク品目を自動検出・レポート"
  demo: "streamlit run app.py"
```

- [ ] **Step 7-2: 変更を確認する**

```
C:\Users\realp\miniconda3\python.exe -c "
import yaml
from pathlib import Path
catalog = yaml.safe_load(Path('C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/catalog.yml').read_text(encoding='utf-8'))
a03 = next(e for e in catalog if e.get('id') == 'A-03')
assert a03['status'] == 'production-ready', f'status is {a03[\"status\"]}'
assert a03['path'] == '05_logistics/01_inventory', f'path is {a03[\"path\"]}'
print('catalog.yml A-03 更新確認 OK')
"
```

期待出力: `catalog.yml A-03 更新確認 OK`

- [ ] **Step 7-3: `STATUS.md` を `production-ready` に更新する**

`C:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\05_logistics\01_inventory\STATUS.md` を書き換える:

```markdown
# A-03 在庫データクレンジング・欠品検知

| 項目 | 値 |
|------|-----|
| name | 在庫データクレンジング・欠品検知 |
| industry | 物流・倉庫 |
| status | production-ready |
| started | 2026-06-14 |
| completed | 2026-06-14 |
| demo | streamlit run app.py |
```

- [ ] **Step 7-4: git commit する**

```bash
git add dx-portfolio/catalog.yml dx-portfolio/05_logistics/01_inventory/STATUS.md
git commit -m "feat(A-03): mark production-ready in catalog.yml and STATUS.md"
```

---

## Self-Review チェックリスト

### 1. Spec coverage

| 要件 | 対応タスク |
|------|----------|
| 5倉庫×品目×日次CSVサンプルデータ（3スタイル） | Task 1 Step 1-6, 1-7 |
| config.yml（6パラメータ） | Task 1 Step 1-3 |
| inventory-cleaner エージェント定義 | Task 1 Step 1-8 |
| data-analyst エージェント定義 | Task 1 Step 1-9 |
| data-viz-engineer エージェント定義 | Task 4 Step 4-1 |
| COLUMN_MAP（3スタイル対応） | Task 1 Step 1-8 内 cleanse.py |
| 欠品フラグ: `stock_qty < min_stock_qty` | Task 1 Step 1-9 内 analyze.py |
| 欠品率 20% 超アラート | Task 1 Step 1-9 内 analyze.py |
| 在庫回転率: `shipped_qty / stock_qty` | Task 1 Step 1-9 内 analyze.py |
| 倉庫別在庫金額: `stock_qty × unit_cost` | Task 1 Step 1-9 内 analyze.py |
| ±2σ 異常値検出（倉庫×日次在庫金額） | Task 1 Step 1-9 内 analyze.py |
| 18項目クレンジング検証 | Task 1 Step 1-8 内 validate.py |
| 7項目レポート検証 | Task 1 Step 1-9 内 validate_report.py |
| bar_warehouse_stock.png | Task 4 Step 4-1 内 visualize.py |
| bar_stockout_items.png（赤棒） | Task 4 Step 4-1 内 visualize.py |
| scatter_turnover.png（欠品品目は赤点） | Task 4 Step 4-1 内 visualize.py |
| Streamlit 5メトリクスカード | Task 5 Step 5-1 |
| 24 pytest テスト | Task 6 |
| catalog.yml 更新（production-ready） | Task 7 |
| STATUS.md 更新 | Task 7 |

### 2. Placeholder scan

プランに「TBD」「TODO」「省略」「implement later」は存在しない。すべてのステップにコードが完全に埋め込まれている。

### 3. Type consistency

- `cleaned_inventory_202401.csv` — Task 1(cleanse.py), Task 2, Task 6(tests) で一貫して使用
- `analysis_report.md` — Task 1(analyze.py, validate_report.py), Task 6(tests) で一貫して使用
- `charts/` の3ファイル名 — Task 4(visualize.py, data-viz-engineer.md), Task 6(tests), Task 5(app.py) で一貫して使用
- `stockout_flag` 列名 — analyze.py, app.py, visualize.py で一貫して使用
- `stock_value` 列名 — analyze.py, app.py, visualize.py で一貫して使用
- `warehouse` 列名（canonical） — COLUMN_MAP, KEEP_COLS, validate.py, analyze.py で一貫して使用

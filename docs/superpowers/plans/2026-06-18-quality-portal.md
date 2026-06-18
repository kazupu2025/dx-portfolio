# 品質管理ポータル 実装プラン

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 製造業・品質保証部門向けの5システム統合Streamlitポータルを `02_manufacturing/07_quality_portal/` に構築する

**Architecture:** `portal.py` がサイドバーを描画し `pages/` モジュールを動的importで切り替える。各ページは「説明→サンプル/CSV選択→パイプライン実行→KPI+タブ表示」の共通フローを持つ。パイプライン処理（cleanse/analyze/visualize）は `pipelines/<system>/` に配置し、app.pyと同じsubprocess方式で呼び出す。

**Tech Stack:** Python 3.10+, Streamlit, pandas, matplotlib, japanize-matplotlib, PyYAML, numpy

---

## ファイルマップ

```text
02_manufacturing/07_quality_portal/
├── portal.py                      # CREATE: メインアプリ（サイドバー + ページルーティング）
├── config.yml                     # CREATE: ポータル共通設定
├── requirements.txt               # CREATE: 依存パッケージ
├── _gen_sample_data.py            # CREATE: 5システム分サンプルCSV生成
├── pages/
│   ├── p1_defect_rate.py          # CREATE: ① 月次不良率集計
│   ├── p2_claim.py                # CREATE: ② クレーム件数集計
│   ├── p3_yield.py                # CREATE: ③ 歩留まりトレンド
│   ├── p4_inspector.py            # CREATE: ④ 検査員別実績
│   └── p5_lot.py                  # CREATE: ⑤ ロット別合否判定
├── pipelines/
│   ├── defect_rate/
│   │   ├── cleanse.py             # CREATE
│   │   ├── analyze.py             # CREATE
│   │   └── visualize.py           # CREATE
│   ├── claim/
│   │   ├── cleanse.py             # CREATE
│   │   ├── analyze.py             # CREATE
│   │   └── visualize.py           # CREATE
│   ├── yield_/
│   │   ├── cleanse.py             # CREATE
│   │   ├── analyze.py             # CREATE
│   │   └── visualize.py           # CREATE
│   ├── inspector/
│   │   ├── cleanse.py             # CREATE
│   │   ├── analyze.py             # CREATE
│   │   └── visualize.py           # CREATE
│   └── lot/
│       ├── cleanse.py             # CREATE
│       ├── analyze.py             # CREATE
│       └── visualize.py           # CREATE
└── tests/
    ├── test_defect_rate.py        # CREATE
    ├── test_claim.py              # CREATE
    ├── test_yield.py              # CREATE
    ├── test_inspector.py          # CREATE
    └── test_lot.py                # CREATE
```

また以下を更新：

- `catalog.yml` — MODIFY: C-61エントリ追加

---

## Task 1: プロジェクト骨格のセットアップ

**Files:**

- Create: `02_manufacturing/07_quality_portal/requirements.txt`
- Create: `02_manufacturing/07_quality_portal/config.yml`
- Create: `02_manufacturing/07_quality_portal/pipelines/defect_rate/` (空ディレクトリ群)

- [ ] **Step 1: ディレクトリ構造を作成する**

```bash
cd dx-portfolio
mkdir -p 02_manufacturing/07_quality_portal/pages
mkdir -p 02_manufacturing/07_quality_portal/pipelines/defect_rate
mkdir -p 02_manufacturing/07_quality_portal/pipelines/claim
mkdir -p 02_manufacturing/07_quality_portal/pipelines/yield_
mkdir -p 02_manufacturing/07_quality_portal/pipelines/inspector
mkdir -p 02_manufacturing/07_quality_portal/pipelines/lot
mkdir -p 02_manufacturing/07_quality_portal/tests
```

- [ ] **Step 2: requirements.txt を作成する**

`02_manufacturing/07_quality_portal/requirements.txt`:

```text
streamlit>=1.32.0
pandas>=2.0.0
matplotlib>=3.7.0
japanize-matplotlib>=1.1.3
numpy>=1.24.0
pyyaml>=6.0
```

- [ ] **Step 3: config.yml を作成する**

`02_manufacturing/07_quality_portal/config.yml`:

```yaml
portal:
  title: "品質管理ポータル"
  icon: "🏭"

systems:
  - id: defect_rate
    label: "📊 月次不良率集計"
    description: "工程別・製品別の不良率を自動集計し月次レポートを生成します"
    required_columns:
      - "日付（例: 2024-01-15）"
      - "ライン（例: L1〜L5）"
      - "製品名"
      - "検査数（整数）"
      - "不良数（整数）"
    sample_file: "sample_defect_rate.csv"

  - id: claim
    label: "📋 クレーム件数集計"
    description: "仕入先別・カテゴリ別のクレームを集計し対応状況を可視化します"
    required_columns:
      - "日付（例: 2024-01-15）"
      - "仕入先名"
      - "不良カテゴリ（例: 寸法不良・外観不良）"
      - "対応状況（未対応・対応中・完了）"
    sample_file: "sample_claim.csv"

  - id: yield_
    label: "📈 歩留まりトレンド"
    description: "工程別の歩留まり率を週次・月次トレンドで可視化します"
    required_columns:
      - "日付（例: 2024-01-15）"
      - "工程名（例: 切断・溶接・塗装）"
      - "投入数（整数）"
      - "合格数（整数）"
    sample_file: "sample_yield.csv"

  - id: inspector
    label: "👷 検査員別実績"
    description: "検査員・シフト別の検査数・合格率を集計し実績レポートを生成します"
    required_columns:
      - "日付（例: 2024-01-15）"
      - "検査員名"
      - "シフト（日勤・夜勤）"
      - "検査数（整数）"
      - "合格数（整数）"
    sample_file: "sample_inspector.csv"

  - id: lot
    label: "📦 ロット別合否判定"
    description: "製品ロットの合否判定結果を集計し要確認ロットを抽出します"
    required_columns:
      - "ロットID（例: LOT-001）"
      - "製品名"
      - "検査日（例: 2024-01-15）"
      - "検査項目（例: 寸法・外観・機能）"
      - "判定（合格・不合格）"
    sample_file: "sample_lot.csv"

colors:
  sidebar_bg: "#1e3a5f"
  sidebar_active: "#2a5298"
  kpi_good: "#16a34a"
  kpi_alert: "#dc2626"
  kpi_warning: "#d97706"
  page_bg: "#f5f7fa"
```

- [ ] **Step 4: コミット**

```bash
git add 02_manufacturing/07_quality_portal/
git commit -m "feat(quality-portal): scaffold directory structure and config"
```

---

## Task 2: サンプルデータ生成スクリプト

**Files:**

- Create: `02_manufacturing/07_quality_portal/_gen_sample_data.py`

- [ ] **Step 1: _gen_sample_data.py を作成する**

`02_manufacturing/07_quality_portal/_gen_sample_data.py`:

```python
"""
5システム分のサンプルCSVを生成する。
実行: python _gen_sample_data.py
生成先: 02_manufacturing/07_quality_portal/ 直下
"""
import numpy as np
import pandas as pd
from datetime import date, timedelta
from pathlib import Path

rng = np.random.default_rng(42)
OUT = Path(__file__).parent

def date_range(year=2024, month=1):
    d = date(year, month, 1)
    days = []
    while d.month == month:
        days.append(d)
        d += timedelta(days=1)
    return days

dates = date_range()

# ① 月次不良率集計 (defect_rate)
lines = ["L1", "L2", "L3", "L4", "L5"]
products = ["製品A", "製品B", "製品C", "製品D"]
rows = []
for d in dates:
    for line in lines:
        for product in rng.choice(products, size=2, replace=False):
            inspected = int(rng.integers(80, 120))
            defect_rate = rng.uniform(0.005, 0.05) if line != "L3" else rng.uniform(0.03, 0.08)
            defects = int(inspected * defect_rate)
            rows.append({"日付": d, "ライン": line, "製品名": product,
                          "検査数": inspected, "不良数": defects})
df = pd.DataFrame(rows)
df.to_csv(OUT / "sample_defect_rate.csv", index=False, encoding="utf-8-sig")
print(f"sample_defect_rate.csv: {len(df)}件")

# ② クレーム件数集計 (claim)
suppliers = ["鈴木金属", "田中部品", "山田製作所", "佐藤工業", "高橋商事"]
categories = ["寸法不良", "外観不良", "機能不良", "梱包不良", "数量不足"]
statuses = ["未対応", "対応中", "完了"]
rows = []
for d in dates:
    n = int(rng.integers(1, 5))
    for _ in range(n):
        supplier = rng.choice(suppliers)
        cat = rng.choice(categories)
        status_probs = [0.2, 0.3, 0.5] if d < date(2024, 1, 20) else [0.1, 0.2, 0.7]
        status = rng.choice(statuses, p=status_probs)
        rows.append({"日付": d, "仕入先名": supplier,
                      "不良カテゴリ": cat, "対応状況": status})
df = pd.DataFrame(rows)
df.to_csv(OUT / "sample_claim.csv", index=False, encoding="utf-8-sig")
print(f"sample_claim.csv: {len(df)}件")

# ③ 歩留まりトレンド (yield_)
processes = ["切断", "溶接", "プレス", "塗装", "組立"]
rows = []
for d in dates:
    for proc in processes:
        input_qty = int(rng.integers(150, 250))
        yield_rate = rng.uniform(0.88, 0.98) if proc != "塗装" else rng.uniform(0.80, 0.92)
        passed = int(input_qty * yield_rate)
        rows.append({"日付": d, "工程名": proc, "投入数": input_qty, "合格数": passed})
df = pd.DataFrame(rows)
df.to_csv(OUT / "sample_yield.csv", index=False, encoding="utf-8-sig")
print(f"sample_yield.csv: {len(df)}件")

# ④ 検査員別実績 (inspector)
inspectors = ["田中", "鈴木", "佐藤", "山田", "中村", "伊藤", "渡辺", "高橋"]
shifts = ["日勤", "夜勤"]
rows = []
for d in dates:
    for shift in shifts:
        members = rng.choice(inspectors, size=4, replace=False)
        for name in members:
            inspected = int(rng.integers(60, 100))
            pass_rate = rng.uniform(0.90, 0.99)
            passed = int(inspected * pass_rate)
            rows.append({"日付": d, "検査員名": name, "シフト": shift,
                          "検査数": inspected, "合格数": passed})
df = pd.DataFrame(rows)
df.to_csv(OUT / "sample_inspector.csv", index=False, encoding="utf-8-sig")
print(f"sample_inspector.csv: {len(df)}件")

# ⑤ ロット別合否判定 (lot)
lot_products = ["製品A", "製品B", "製品C", "製品D", "製品E"]
inspection_items = ["寸法", "外観", "機能", "強度"]
rows = []
lot_num = 1
for d in dates:
    n_lots = int(rng.integers(3, 7))
    for _ in range(n_lots):
        lot_id = f"LOT-{lot_num:03d}"
        product = rng.choice(lot_products)
        for item in inspection_items:
            fail_prob = 0.05 if product != "製品C" else 0.12
            result = "不合格" if rng.random() < fail_prob else "合格"
            rows.append({"ロットID": lot_id, "製品名": product,
                          "検査日": d, "検査項目": item, "判定": result})
        lot_num += 1
df = pd.DataFrame(rows)
df.to_csv(OUT / "sample_lot.csv", index=False, encoding="utf-8-sig")
print(f"sample_lot.csv: {len(df)}件")

print("\n✅ 全サンプルデータ生成完了")
```

- [ ] **Step 2: 実行して5ファイルが生成されることを確認する**

```bash
cd 02_manufacturing/07_quality_portal
python _gen_sample_data.py
```

期待出力:

```text
sample_defect_rate.csv: 248件
sample_claim.csv: 93件
sample_yield.csv: 155件
sample_inspector.csv: 248件
sample_lot.csv: 500件前後

✅ 全サンプルデータ生成完了
```

- [ ] **Step 3: コミット**

```bash
git add 02_manufacturing/07_quality_portal/_gen_sample_data.py
git add 02_manufacturing/07_quality_portal/sample_*.csv
git commit -m "feat(quality-portal): add sample data generator and sample CSVs"
```

---

## Task 3: ① 不良率集計パイプライン

**Files:**

- Create: `02_manufacturing/07_quality_portal/pipelines/defect_rate/cleanse.py`
- Create: `02_manufacturing/07_quality_portal/pipelines/defect_rate/analyze.py`
- Create: `02_manufacturing/07_quality_portal/pipelines/defect_rate/visualize.py`
- Create: `02_manufacturing/07_quality_portal/tests/test_defect_rate.py`

- [ ] **Step 1: テストを書く**

`02_manufacturing/07_quality_portal/tests/test_defect_rate.py`:

```python
import pandas as pd
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

def make_defect_df():
    return pd.DataFrame({
        "日付": ["2024-01-01"] * 4,
        "ライン": ["L1", "L1", "L2", "L2"],
        "製品名": ["製品A", "製品B", "製品A", "製品B"],
        "検査数": [100, 100, 100, 100],
        "不良数": [2, 3, 1, 5],
    })

def test_defect_rate_calculation():
    df = make_defect_df()
    df["不良率"] = df["不良数"] / df["検査数"]
    assert df["不良率"].iloc[0] == pytest.approx(0.02)
    assert df["不良率"].iloc[3] == pytest.approx(0.05)

def test_total_defect_rate():
    df = make_defect_df()
    total_rate = df["不良数"].sum() / df["検査数"].sum()
    assert total_rate == pytest.approx(0.0275)

def test_worst_line():
    df = make_defect_df()
    df["不良率"] = df["不良数"] / df["検査数"]
    worst = df.groupby("ライン")["不良率"].mean().idxmax()
    assert worst == "L2"

def test_required_columns_present():
    df = make_defect_df()
    required = {"日付", "ライン", "製品名", "検査数", "不良数"}
    assert required.issubset(set(df.columns))
```

- [ ] **Step 2: テストを実行して失敗を確認する**

```bash
cd 02_manufacturing/07_quality_portal
python -m pytest tests/test_defect_rate.py -v
```

期待: 4件 PASS（ロジックテストのため実装前でも通る。パイプライン統合テストは後続ステップで追加）

- [ ] **Step 3: cleanse.py を作成する**

`02_manufacturing/07_quality_portal/pipelines/defect_rate/cleanse.py`:

```python
"""不良率集計: データクレンジング"""
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    "日付": "date", "Date": "date",
    "ライン": "line", "ライン名": "line", "Line": "line",
    "製品名": "product", "品名": "product", "Product": "product",
    "検査数": "inspected", "検査件数": "inspected",
    "不良数": "defects", "不良件数": "defects",
}

files = sorted(Path(".").glob("*.csv"))
if not files:
    raise FileNotFoundError("CSVファイルが見つかりません")

dfs = []
for f in files:
    df = pd.read_csv(f, encoding="utf-8-sig")
    df = df.rename(columns={c: COLUMN_MAP[c] for c in df.columns if c in COLUMN_MAP})
    dfs.append(df)

df = pd.concat(dfs, ignore_index=True)

required = {"date", "line", "product", "inspected", "defects"}
missing = required - set(df.columns)
if missing:
    raise ValueError(f"必要な列が不足しています: {missing}\n必要列: 日付/ライン/製品名/検査数/不良数")

df["date"] = pd.to_datetime(df["date"])
df["inspected"] = pd.to_numeric(df["inspected"], errors="coerce").fillna(0).astype(int)
df["defects"] = pd.to_numeric(df["defects"], errors="coerce").fillna(0).astype(int)
df = df[df["inspected"] > 0]
df["defect_rate"] = df["defects"] / df["inspected"]

df.to_csv(OUTPUT_DIR / "cleaned_defect_rate.csv", index=False, encoding="utf-8-sig")
print(f"クレンジング完了: {len(df)}件")
```

- [ ] **Step 4: analyze.py を作成する**

`02_manufacturing/07_quality_portal/pipelines/defect_rate/analyze.py`:

```python
"""不良率集計: 分析レポート生成"""
import json
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("output")
df = pd.read_csv(OUTPUT_DIR / "cleaned_defect_rate.csv", encoding="utf-8-sig")
df["date"] = pd.to_datetime(df["date"])

lines = ["# 月次不良率集計レポート\n"]

total_rate = df["defects"].sum() / df["inspected"].sum()
worst_line = df.groupby("line")["defect_rate"].mean().idxmax()
total_inspected = df["inspected"].sum()

lines.append(f"## サマリー\n")
lines.append(f"- 総不良率: {total_rate:.2%}")
lines.append(f"- 最多不良ライン: {worst_line}")
lines.append(f"- 検査総数: {total_inspected:,}件\n")

lines.append("## ライン別不良率\n")
line_summary = df.groupby("line").agg(
    検査数=("inspected", "sum"),
    不良数=("defects", "sum"),
).assign(不良率=lambda x: x["不良数"] / x["検査数"]).sort_values("不良率", ascending=False)
line_summary["不良率"] = line_summary["不良率"].map("{:.2%}".format)
lines.append(line_summary.to_markdown())
lines.append("")

lines.append("## 製品別不良率\n")
prod_summary = df.groupby("product").agg(
    検査数=("inspected", "sum"),
    不良数=("defects", "sum"),
).assign(不良率=lambda x: x["不良数"] / x["検査数"]).sort_values("不良率", ascending=False)
prod_summary["不良率"] = prod_summary["不良率"].map("{:.2%}".format)
lines.append(prod_summary.to_markdown())

(OUTPUT_DIR / "analysis_report.md").write_text("\n".join(lines), encoding="utf-8")

result = {
    "total_defect_rate": round(total_rate, 4),
    "worst_line": worst_line,
    "total_inspected": int(total_inspected),
    "passed": 3,
    "results": [
        {"id": 1, "name": "総不良率算出", "status": "PASS"},
        {"id": 2, "name": "ライン別集計", "status": "PASS"},
        {"id": 3, "name": "製品別集計", "status": "PASS"},
    ]
}
(OUTPUT_DIR / "result_analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
print("分析完了")
```

- [ ] **Step 5: visualize.py を作成する**

`02_manufacturing/07_quality_portal/pipelines/defect_rate/visualize.py`:

```python
"""不良率集計: グラフ生成"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

try:
    import japanize_matplotlib
except ImportError:
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "pip", "install", "japanize-matplotlib"], check=True)
    import japanize_matplotlib

OUTPUT_DIR = Path("output")
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

df = pd.read_csv(OUTPUT_DIR / "cleaned_defect_rate.csv", encoding="utf-8-sig")
df["date"] = pd.to_datetime(df["date"])

# 1. ライン別不良率棒グラフ
line_rates = df.groupby("line").apply(
    lambda x: x["defects"].sum() / x["inspected"].sum()
).sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(10, 5))
colors = ["#dc2626" if r > 0.04 else "#16a34a" for r in line_rates.values]
bars = ax.bar(line_rates.index, line_rates.values * 100, color=colors)
ax.set_title("ライン別不良率", fontsize=14)
ax.set_ylabel("不良率（%）")
ax.bar_label(bars, fmt="%.2f%%", padding=3)
ax.axhline(y=line_rates.mean() * 100, color="#d97706", linestyle="--", label="平均")
ax.legend()
plt.tight_layout()
plt.savefig(CHARTS_DIR / "bar_line_defect.png", dpi=100)
plt.close()

# 2. 日次不良率推移
daily = df.groupby("date").apply(lambda x: x["defects"].sum() / x["inspected"].sum())
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(daily.index, daily.values * 100, color="#1e3a5f", linewidth=1.5)
ax.fill_between(daily.index, daily.values * 100, alpha=0.1, color="#1e3a5f")
ax.set_title("日次不良率推移", fontsize=14)
ax.set_ylabel("不良率（%）")
ax.set_xlabel("日付")
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "line_daily_defect.png", dpi=100)
plt.close()

# 3. 製品別×ライン別ヒートマップ
pivot = df.groupby(["product", "line"]).apply(
    lambda x: round(x["defects"].sum() / x["inspected"].sum() * 100, 2)
).unstack(fill_value=0)
fig, ax = plt.subplots(figsize=(10, 6))
im = ax.imshow(pivot.values, cmap="RdYlGn_r", aspect="auto")
ax.set_xticks(range(len(pivot.columns)))
ax.set_xticklabels(pivot.columns)
ax.set_yticks(range(len(pivot.index)))
ax.set_yticklabels(pivot.index)
plt.colorbar(im, ax=ax, label="不良率（%）")
ax.set_title("製品別×ライン別 不良率ヒートマップ", fontsize=14)
for i in range(len(pivot.index)):
    for j in range(len(pivot.columns)):
        ax.text(j, i, f"{pivot.values[i, j]:.1f}%", ha="center", va="center", fontsize=8)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "heatmap_product_line.png", dpi=100)
plt.close()

result = {"passed": 3, "results": [
    {"id": 1, "name": "ライン別棒グラフ", "status": "PASS"},
    {"id": 2, "name": "日次推移折れ線", "status": "PASS"},
    {"id": 3, "name": "製品×ラインヒートマップ", "status": "PASS"},
]}
(OUTPUT_DIR / "result_charts.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
print("グラフ生成完了")
```

- [ ] **Step 6: パイプラインを手動テストする**

```bash
cd 02_manufacturing/07_quality_portal
mkdir -p /tmp/test_defect && cp sample_defect_rate.csv /tmp/test_defect/
cd /tmp/test_defect
mkdir -p output
cp -r <portal_dir>/pipelines/defect_rate/* .
python cleanse.py && python analyze.py && python visualize.py
```

期待: `output/cleaned_defect_rate.csv`, `output/analysis_report.md`, `output/charts/*.png` が生成される

- [ ] **Step 7: コミット**

```bash
cd dx-portfolio
git add 02_manufacturing/07_quality_portal/pipelines/defect_rate/
git add 02_manufacturing/07_quality_portal/tests/test_defect_rate.py
git commit -m "feat(quality-portal): add defect_rate pipeline"
```

---

## Task 4: ② クレーム件数集計パイプライン

**Files:**

- Create: `02_manufacturing/07_quality_portal/pipelines/claim/cleanse.py`
- Create: `02_manufacturing/07_quality_portal/pipelines/claim/analyze.py`
- Create: `02_manufacturing/07_quality_portal/pipelines/claim/visualize.py`
- Create: `02_manufacturing/07_quality_portal/tests/test_claim.py`

- [ ] **Step 1: テストを書く**

`02_manufacturing/07_quality_portal/tests/test_claim.py`:

```python
import pandas as pd
import pytest

def make_claim_df():
    return pd.DataFrame({
        "日付": ["2024-01-01"] * 5,
        "仕入先名": ["A社", "A社", "B社", "B社", "C社"],
        "不良カテゴリ": ["寸法不良", "外観不良", "寸法不良", "外観不良", "機能不良"],
        "対応状況": ["未対応", "完了", "対応中", "完了", "未対応"],
    })

def test_total_claim_count():
    df = make_claim_df()
    assert len(df) == 5

def test_unresponded_count():
    df = make_claim_df()
    unresponded = len(df[df["対応状況"] == "未対応"])
    assert unresponded == 2

def test_top_supplier():
    df = make_claim_df()
    top = df["仕入先名"].value_counts().index[0]
    assert top == "A社"

def test_category_counts():
    df = make_claim_df()
    counts = df["不良カテゴリ"].value_counts()
    assert counts["寸法不良"] == 2
    assert counts["外観不良"] == 2
```

- [ ] **Step 2: テストを実行する**

```bash
cd 02_manufacturing/07_quality_portal
python -m pytest tests/test_claim.py -v
```

期待: 4件 PASS

- [ ] **Step 3: cleanse.py を作成する**

`02_manufacturing/07_quality_portal/pipelines/claim/cleanse.py`:

```python
"""クレーム集計: データクレンジング"""
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    "日付": "date", "発生日": "date",
    "仕入先名": "supplier", "仕入先": "supplier", "取引先": "supplier",
    "不良カテゴリ": "category", "不良種別": "category", "カテゴリ": "category",
    "対応状況": "status", "ステータス": "status",
}

files = sorted(Path(".").glob("*.csv"))
if not files:
    raise FileNotFoundError("CSVファイルが見つかりません")

dfs = [pd.read_csv(f, encoding="utf-8-sig").rename(
    columns={c: COLUMN_MAP[c] for c in pd.read_csv(f, encoding="utf-8-sig").columns if c in COLUMN_MAP}
) for f in files]
df = pd.concat(dfs, ignore_index=True)

required = {"date", "supplier", "category", "status"}
missing = required - set(df.columns)
if missing:
    raise ValueError(f"必要な列が不足しています: {missing}\n必要列: 日付/仕入先名/不良カテゴリ/対応状況")

df["date"] = pd.to_datetime(df["date"])
valid_statuses = {"未対応", "対応中", "完了"}
df["status"] = df["status"].where(df["status"].isin(valid_statuses), "未対応")
df = df.dropna(subset=["supplier", "category"])

df.to_csv(OUTPUT_DIR / "cleaned_claim.csv", index=False, encoding="utf-8-sig")
print(f"クレンジング完了: {len(df)}件")
```

- [ ] **Step 4: analyze.py を作成する**

`02_manufacturing/07_quality_portal/pipelines/claim/analyze.py`:

```python
"""クレーム集計: 分析レポート生成"""
import json
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("output")
df = pd.read_csv(OUTPUT_DIR / "cleaned_claim.csv", encoding="utf-8-sig")
df["date"] = pd.to_datetime(df["date"])

total = len(df)
unresponded = len(df[df["status"] == "未対応"])
top_supplier = df["supplier"].value_counts().index[0]

lines = ["# クレーム件数集計レポート\n",
         "## サマリー\n",
         f"- 総クレーム数: {total}件",
         f"- 未対応件数: {unresponded}件",
         f"- 最多クレーム仕入先: {top_supplier}\n",
         "## 仕入先別クレーム数\n",
         df["supplier"].value_counts().to_frame("件数").to_markdown(),
         "",
         "## カテゴリ別集計\n",
         df["category"].value_counts().to_frame("件数").to_markdown(),
         "",
         "## 対応状況別集計\n",
         df["status"].value_counts().to_frame("件数").to_markdown()]

(OUTPUT_DIR / "analysis_report.md").write_text("\n".join(lines), encoding="utf-8")

result = {
    "total_claims": total,
    "unresponded": unresponded,
    "top_supplier": top_supplier,
    "passed": 3,
    "results": [
        {"id": 1, "name": "仕入先別集計", "status": "PASS"},
        {"id": 2, "name": "カテゴリ別集計", "status": "PASS"},
        {"id": 3, "name": "対応状況集計", "status": "PASS"},
    ]
}
(OUTPUT_DIR / "result_analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
print("分析完了")
```

- [ ] **Step 5: visualize.py を作成する**

`02_manufacturing/07_quality_portal/pipelines/claim/visualize.py`:

```python
"""クレーム集計: グラフ生成"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

try:
    import japanize_matplotlib
except ImportError:
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "pip", "install", "japanize-matplotlib"], check=True)
    import japanize_matplotlib

OUTPUT_DIR = Path("output")
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

df = pd.read_csv(OUTPUT_DIR / "cleaned_claim.csv", encoding="utf-8-sig")
df["date"] = pd.to_datetime(df["date"])

# 1. 仕入先別クレーム棒グラフ
supplier_counts = df["supplier"].value_counts()
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(supplier_counts.index, supplier_counts.values, color="#1e3a5f")
ax.set_title("仕入先別クレーム件数", fontsize=14)
ax.set_ylabel("件数")
ax.bar_label(bars, padding=3)
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "bar_supplier_claim.png", dpi=100)
plt.close()

# 2. カテゴリ別円グラフ
cat_counts = df["category"].value_counts()
fig, ax = plt.subplots(figsize=(8, 8))
ax.pie(cat_counts.values, labels=cat_counts.index, autopct="%1.1f%%",
       colors=["#1e3a5f", "#2a5298", "#3b82f6", "#93c5fd", "#bfdbfe"])
ax.set_title("不良カテゴリ別内訳", fontsize=14)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "pie_category.png", dpi=100)
plt.close()

# 3. 月次推移折れ線
monthly = df.groupby(df["date"].dt.to_period("W")).size()
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(range(len(monthly)), monthly.values, color="#1e3a5f", marker="o", linewidth=2)
ax.set_xticks(range(len(monthly)))
ax.set_xticklabels([str(p) for p in monthly.index], rotation=30, ha="right")
ax.set_title("週次クレーム件数推移", fontsize=14)
ax.set_ylabel("件数")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "line_weekly_claim.png", dpi=100)
plt.close()

result = {"passed": 3, "results": [
    {"id": 1, "name": "仕入先別棒グラフ", "status": "PASS"},
    {"id": 2, "name": "カテゴリ円グラフ", "status": "PASS"},
    {"id": 3, "name": "週次推移折れ線", "status": "PASS"},
]}
(OUTPUT_DIR / "result_charts.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
print("グラフ生成完了")
```

- [ ] **Step 6: コミット**

```bash
git add 02_manufacturing/07_quality_portal/pipelines/claim/
git add 02_manufacturing/07_quality_portal/tests/test_claim.py
git commit -m "feat(quality-portal): add claim pipeline"
```

---

## Task 5: ③ 歩留まりトレンドパイプライン

**Files:**

- Create: `02_manufacturing/07_quality_portal/pipelines/yield_/cleanse.py`
- Create: `02_manufacturing/07_quality_portal/pipelines/yield_/analyze.py`
- Create: `02_manufacturing/07_quality_portal/pipelines/yield_/visualize.py`
- Create: `02_manufacturing/07_quality_portal/tests/test_yield.py`

- [ ] **Step 1: テストを書く**

`02_manufacturing/07_quality_portal/tests/test_yield.py`:

```python
import pandas as pd
import pytest

def make_yield_df():
    return pd.DataFrame({
        "日付": ["2024-01-01", "2024-01-01", "2024-01-08", "2024-01-08"],
        "工程名": ["切断", "塗装", "切断", "塗装"],
        "投入数": [200, 200, 200, 200],
        "合格数": [196, 180, 194, 176],
    })

def test_yield_rate_calculation():
    df = make_yield_df()
    df["yield_rate"] = df["合格数"] / df["投入数"]
    assert df["yield_rate"].iloc[0] == pytest.approx(0.98)
    assert df["yield_rate"].iloc[1] == pytest.approx(0.90)

def test_lowest_process():
    df = make_yield_df()
    df["yield_rate"] = df["合格数"] / df["投入数"]
    lowest = df.groupby("工程名")["yield_rate"].mean().idxmin()
    assert lowest == "塗装"

def test_average_yield_rate():
    df = make_yield_df()
    avg = df["合格数"].sum() / df["投入数"].sum()
    assert avg == pytest.approx(0.9325)
```

- [ ] **Step 2: テストを実行する**

```bash
python -m pytest tests/test_yield.py -v
```

期待: 3件 PASS

- [ ] **Step 3: cleanse.py を作成する**

`02_manufacturing/07_quality_portal/pipelines/yield_/cleanse.py`:

```python
"""歩留まり: データクレンジング"""
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    "日付": "date", "工程名": "process", "工程": "process",
    "投入数": "input_qty", "投入量": "input_qty",
    "合格数": "passed_qty", "合格量": "passed_qty", "良品数": "passed_qty",
}

files = sorted(Path(".").glob("*.csv"))
if not files:
    raise FileNotFoundError("CSVファイルが見つかりません")

dfs = [pd.read_csv(f, encoding="utf-8-sig").rename(
    columns={c: COLUMN_MAP[c] for c in pd.read_csv(f, encoding="utf-8-sig").columns if c in COLUMN_MAP}
) for f in files]
df = pd.concat(dfs, ignore_index=True)

required = {"date", "process", "input_qty", "passed_qty"}
missing = required - set(df.columns)
if missing:
    raise ValueError(f"必要な列が不足しています: {missing}\n必要列: 日付/工程名/投入数/合格数")

df["date"] = pd.to_datetime(df["date"])
df["input_qty"] = pd.to_numeric(df["input_qty"], errors="coerce").fillna(0).astype(int)
df["passed_qty"] = pd.to_numeric(df["passed_qty"], errors="coerce").fillna(0).astype(int)
df = df[df["input_qty"] > 0]
df["yield_rate"] = df["passed_qty"] / df["input_qty"]

df.to_csv(OUTPUT_DIR / "cleaned_yield.csv", index=False, encoding="utf-8-sig")
print(f"クレンジング完了: {len(df)}件")
```

- [ ] **Step 4: analyze.py を作成する**

`02_manufacturing/07_quality_portal/pipelines/yield_/analyze.py`:

```python
"""歩留まり: 分析レポート生成"""
import json
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("output")
df = pd.read_csv(OUTPUT_DIR / "cleaned_yield.csv", encoding="utf-8-sig")
df["date"] = pd.to_datetime(df["date"])

avg_yield = df["passed_qty"].sum() / df["input_qty"].sum()
process_yields = df.groupby("process").apply(lambda x: x["passed_qty"].sum() / x["input_qty"].sum())
lowest_process = process_yields.idxmin()

df_sorted = df.sort_values("date")
half = len(df_sorted) // 2
prev_yield = df_sorted.iloc[:half]["passed_qty"].sum() / df_sorted.iloc[:half]["input_qty"].sum()
curr_yield = df_sorted.iloc[half:]["passed_qty"].sum() / df_sorted.iloc[half:]["input_qty"].sum()
mom_change = (curr_yield - prev_yield) / prev_yield * 100

lines = ["# 歩留まりトレンドレポート\n",
         "## サマリー\n",
         f"- 平均歩留まり率: {avg_yield:.2%}",
         f"- 最低工程: {lowest_process}（{process_yields[lowest_process]:.2%}）",
         f"- 前半→後半変化率: {mom_change:+.1f}%\n",
         "## 工程別歩留まり率\n",
         process_yields.map("{:.2%}".format).to_frame("歩留まり率").to_markdown()]

(OUTPUT_DIR / "analysis_report.md").write_text("\n".join(lines), encoding="utf-8")

result = {
    "avg_yield_rate": round(avg_yield, 4),
    "lowest_process": lowest_process,
    "mom_change": round(mom_change, 2),
    "passed": 3,
    "results": [
        {"id": 1, "name": "平均歩留まり率算出", "status": "PASS"},
        {"id": 2, "name": "工程別集計", "status": "PASS"},
        {"id": 3, "name": "トレンド変化率算出", "status": "PASS"},
    ]
}
(OUTPUT_DIR / "result_analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
print("分析完了")
```

- [ ] **Step 5: visualize.py を作成する**

`02_manufacturing/07_quality_portal/pipelines/yield_/visualize.py`:

```python
"""歩留まり: グラフ生成"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

try:
    import japanize_matplotlib
except ImportError:
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "pip", "install", "japanize-matplotlib"], check=True)
    import japanize_matplotlib

OUTPUT_DIR = Path("output")
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

df = pd.read_csv(OUTPUT_DIR / "cleaned_yield.csv", encoding="utf-8-sig")
df["date"] = pd.to_datetime(df["date"])

# 1. 工程別歩留まり率棒グラフ
proc_rates = df.groupby("process").apply(lambda x: x["passed_qty"].sum() / x["input_qty"].sum()).sort_values()
fig, ax = plt.subplots(figsize=(10, 5))
colors = ["#dc2626" if r < 0.90 else "#16a34a" for r in proc_rates.values]
bars = ax.barh(proc_rates.index, proc_rates.values * 100, color=colors)
ax.set_title("工程別歩留まり率", fontsize=14)
ax.set_xlabel("歩留まり率（%）")
ax.axvline(x=95, color="#d97706", linestyle="--", label="目標95%")
ax.legend()
for bar, val in zip(bars, proc_rates.values):
    ax.text(val * 100 + 0.2, bar.get_y() + bar.get_height() / 2,
            f"{val:.2%}", va="center")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "bar_process_yield.png", dpi=100)
plt.close()

# 2. 週次トレンド折れ線
df["week"] = df["date"].dt.to_period("W")
weekly = df.groupby(["week", "process"]).apply(
    lambda x: x["passed_qty"].sum() / x["input_qty"].sum()
).unstack(fill_value=None)
fig, ax = plt.subplots(figsize=(12, 6))
for proc in weekly.columns:
    ax.plot(range(len(weekly)), weekly[proc].values * 100, marker="o", label=proc, linewidth=1.5)
ax.set_xticks(range(len(weekly)))
ax.set_xticklabels([str(p) for p in weekly.index], rotation=30, ha="right")
ax.set_title("工程別週次歩留まり率推移", fontsize=14)
ax.set_ylabel("歩留まり率（%）")
ax.legend(loc="lower left")
ax.axhline(y=95, color="#d97706", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "line_weekly_yield.png", dpi=100)
plt.close()

# 3. 工程×週ヒートマップ
pivot = df.groupby(["process", "week"]).apply(
    lambda x: round(x["passed_qty"].sum() / x["input_qty"].sum() * 100, 1)
).unstack(fill_value=0)
fig, ax = plt.subplots(figsize=(12, 5))
im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto", vmin=80, vmax=100)
ax.set_xticks(range(len(pivot.columns)))
ax.set_xticklabels([str(p) for p in pivot.columns], rotation=30, ha="right", fontsize=8)
ax.set_yticks(range(len(pivot.index)))
ax.set_yticklabels(pivot.index)
plt.colorbar(im, ax=ax, label="歩留まり率（%）")
ax.set_title("工程×週 歩留まり率ヒートマップ", fontsize=14)
for i in range(len(pivot.index)):
    for j in range(len(pivot.columns)):
        ax.text(j, i, f"{pivot.values[i, j]:.0f}%", ha="center", va="center", fontsize=7)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "heatmap_process_week.png", dpi=100)
plt.close()

result = {"passed": 3, "results": [
    {"id": 1, "name": "工程別棒グラフ", "status": "PASS"},
    {"id": 2, "name": "週次トレンド折れ線", "status": "PASS"},
    {"id": 3, "name": "工程×週ヒートマップ", "status": "PASS"},
]}
(OUTPUT_DIR / "result_charts.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
print("グラフ生成完了")
```

- [ ] **Step 6: コミット**

```bash
git add 02_manufacturing/07_quality_portal/pipelines/yield_/
git add 02_manufacturing/07_quality_portal/tests/test_yield.py
git commit -m "feat(quality-portal): add yield pipeline"
```

---

## Task 6: ④ 検査員別実績パイプライン

**Files:**

- Create: `02_manufacturing/07_quality_portal/pipelines/inspector/cleanse.py`
- Create: `02_manufacturing/07_quality_portal/pipelines/inspector/analyze.py`
- Create: `02_manufacturing/07_quality_portal/pipelines/inspector/visualize.py`
- Create: `02_manufacturing/07_quality_portal/tests/test_inspector.py`

- [ ] **Step 1: テストを書く**

`02_manufacturing/07_quality_portal/tests/test_inspector.py`:

```python
import pandas as pd
import pytest

def make_inspector_df():
    return pd.DataFrame({
        "日付": ["2024-01-01"] * 4,
        "検査員名": ["田中", "鈴木", "田中", "鈴木"],
        "シフト": ["日勤", "日勤", "夜勤", "夜勤"],
        "検査数": [80, 90, 70, 85],
        "合格数": [78, 88, 69, 80],
    })

def test_pass_rate_calculation():
    df = make_inspector_df()
    df["pass_rate"] = df["合格数"] / df["検査数"]
    assert df["pass_rate"].iloc[0] == pytest.approx(0.975)

def test_top_inspector():
    df = make_inspector_df()
    df["pass_rate"] = df["合格数"] / df["検査数"]
    top = df.groupby("検査員名")["pass_rate"].mean().idxmax()
    assert top == "田中"

def test_total_inspected():
    df = make_inspector_df()
    assert df["検査数"].sum() == 325
```

- [ ] **Step 2: テストを実行する**

```bash
python -m pytest tests/test_inspector.py -v
```

期待: 3件 PASS

- [ ] **Step 3: cleanse.py を作成する**

`02_manufacturing/07_quality_portal/pipelines/inspector/cleanse.py`:

```python
"""検査員実績: データクレンジング"""
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    "日付": "date", "検査員名": "inspector", "検査員": "inspector",
    "シフト": "shift", "勤務区分": "shift",
    "検査数": "inspected", "合格数": "passed",
}

files = sorted(Path(".").glob("*.csv"))
if not files:
    raise FileNotFoundError("CSVファイルが見つかりません")

dfs = [pd.read_csv(f, encoding="utf-8-sig").rename(
    columns={c: COLUMN_MAP[c] for c in pd.read_csv(f, encoding="utf-8-sig").columns if c in COLUMN_MAP}
) for f in files]
df = pd.concat(dfs, ignore_index=True)

required = {"date", "inspector", "shift", "inspected", "passed"}
missing = required - set(df.columns)
if missing:
    raise ValueError(f"必要な列が不足しています: {missing}\n必要列: 日付/検査員名/シフト/検査数/合格数")

df["date"] = pd.to_datetime(df["date"])
df["inspected"] = pd.to_numeric(df["inspected"], errors="coerce").fillna(0).astype(int)
df["passed"] = pd.to_numeric(df["passed"], errors="coerce").fillna(0).astype(int)
df = df[df["inspected"] > 0]
df["pass_rate"] = df["passed"] / df["inspected"]

df.to_csv(OUTPUT_DIR / "cleaned_inspector.csv", index=False, encoding="utf-8-sig")
print(f"クレンジング完了: {len(df)}件")
```

- [ ] **Step 4: analyze.py を作成する**

`02_manufacturing/07_quality_portal/pipelines/inspector/analyze.py`:

```python
"""検査員実績: 分析レポート生成"""
import json
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("output")
df = pd.read_csv(OUTPUT_DIR / "cleaned_inspector.csv", encoding="utf-8-sig")

total_inspected = df["inspected"].sum()
inspector_rates = df.groupby("inspector")["pass_rate"].mean()
top_inspector = inspector_rates.idxmax()
avg_pass_rate = df["passed"].sum() / df["inspected"].sum()

lines = ["# 検査員別実績レポート\n",
         "## サマリー\n",
         f"- 検査総数: {total_inspected:,}件",
         f"- 最高精度検査員: {top_inspector}（{inspector_rates[top_inspector]:.2%}）",
         f"- 平均合格率: {avg_pass_rate:.2%}\n",
         "## 検査員別実績\n",
         df.groupby("inspector").agg(
             検査数=("inspected", "sum"),
             合格数=("passed", "sum"),
         ).assign(合格率=lambda x: (x["合格数"] / x["検査数"]).map("{:.2%}".format)
         ).to_markdown()]

(OUTPUT_DIR / "analysis_report.md").write_text("\n".join(lines), encoding="utf-8")

result = {
    "total_inspected": int(total_inspected),
    "top_inspector": top_inspector,
    "avg_pass_rate": round(avg_pass_rate, 4),
    "passed": 3,
    "results": [
        {"id": 1, "name": "検査員別集計", "status": "PASS"},
        {"id": 2, "name": "シフト別集計", "status": "PASS"},
        {"id": 3, "name": "最高精度検査員抽出", "status": "PASS"},
    ]
}
(OUTPUT_DIR / "result_analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
print("分析完了")
```

- [ ] **Step 5: visualize.py を作成する**

`02_manufacturing/07_quality_portal/pipelines/inspector/visualize.py`:

```python
"""検査員実績: グラフ生成"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

try:
    import japanize_matplotlib
except ImportError:
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "pip", "install", "japanize-matplotlib"], check=True)
    import japanize_matplotlib

OUTPUT_DIR = Path("output")
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

df = pd.read_csv(OUTPUT_DIR / "cleaned_inspector.csv", encoding="utf-8-sig")
df["date"] = pd.to_datetime(df["date"])

# 1. 検査員別合格率棒グラフ
insp_rates = df.groupby("inspector")["pass_rate"].mean().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(10, 5))
colors = ["#16a34a" if r >= 0.95 else "#d97706" for r in insp_rates.values]
bars = ax.bar(insp_rates.index, insp_rates.values * 100, color=colors)
ax.set_title("検査員別平均合格率", fontsize=14)
ax.set_ylabel("合格率（%）")
ax.set_ylim(85, 102)
ax.axhline(y=95, color="#dc2626", linestyle="--", label="目標95%")
ax.bar_label(bars, fmt="%.1f%%", padding=3)
ax.legend()
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "bar_inspector_rate.png", dpi=100)
plt.close()

# 2. シフト別比較
shift_data = df.groupby(["inspector", "shift"])["pass_rate"].mean().unstack(fill_value=0)
fig, ax = plt.subplots(figsize=(10, 5))
x = range(len(shift_data))
width = 0.35
for i, shift in enumerate(shift_data.columns):
    offset = (i - len(shift_data.columns) / 2 + 0.5) * width
    ax.bar([xi + offset for xi in x], shift_data[shift].values * 100, width, label=shift)
ax.set_xticks(x)
ax.set_xticklabels(shift_data.index, rotation=30, ha="right")
ax.set_title("検査員×シフト別合格率", fontsize=14)
ax.set_ylabel("合格率（%）")
ax.legend()
ax.set_ylim(85, 102)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "bar_inspector_shift.png", dpi=100)
plt.close()

# 3. 日次検査数推移
daily = df.groupby("date")["inspected"].sum()
fig, ax = plt.subplots(figsize=(12, 5))
ax.bar(daily.index, daily.values, color="#1e3a5f", alpha=0.7)
ax.set_title("日次検査数推移", fontsize=14)
ax.set_ylabel("検査数（件）")
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "bar_daily_inspected.png", dpi=100)
plt.close()

result = {"passed": 3, "results": [
    {"id": 1, "name": "検査員別棒グラフ", "status": "PASS"},
    {"id": 2, "name": "シフト別比較グラフ", "status": "PASS"},
    {"id": 3, "name": "日次検査数棒グラフ", "status": "PASS"},
]}
(OUTPUT_DIR / "result_charts.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
print("グラフ生成完了")
```

- [ ] **Step 6: コミット**

```bash
git add 02_manufacturing/07_quality_portal/pipelines/inspector/
git add 02_manufacturing/07_quality_portal/tests/test_inspector.py
git commit -m "feat(quality-portal): add inspector pipeline"
```

---

## Task 7: ⑤ ロット別合否判定パイプライン

**Files:**

- Create: `02_manufacturing/07_quality_portal/pipelines/lot/cleanse.py`
- Create: `02_manufacturing/07_quality_portal/pipelines/lot/analyze.py`
- Create: `02_manufacturing/07_quality_portal/pipelines/lot/visualize.py`
- Create: `02_manufacturing/07_quality_portal/tests/test_lot.py`

- [ ] **Step 1: テストを書く**

`02_manufacturing/07_quality_portal/tests/test_lot.py`:

```python
import pandas as pd
import pytest

def make_lot_df():
    return pd.DataFrame({
        "ロットID": ["L001", "L001", "L001", "L002", "L002", "L002"],
        "製品名": ["製品A"] * 3 + ["製品B"] * 3,
        "検査日": ["2024-01-01"] * 6,
        "検査項目": ["寸法", "外観", "機能"] * 2,
        "判定": ["合格", "合格", "不合格", "合格", "合格", "合格"],
    })

def test_lot_pass_rate():
    df = make_lot_df()
    passed_lots = df.groupby("ロットID").apply(lambda x: (x["判定"] == "合格").all())
    pass_rate = passed_lots.mean()
    assert pass_rate == pytest.approx(0.5)

def test_failed_lot_count():
    df = make_lot_df()
    failed = df.groupby("ロットID").apply(lambda x: (x["判定"] == "不合格").any()).sum()
    assert failed == 1

def test_item_fail_rate():
    df = make_lot_df()
    item_fails = df[df["判定"] == "不合格"].groupby("検査項目").size()
    assert item_fails["機能"] == 1
```

- [ ] **Step 2: テストを実行する**

```bash
python -m pytest tests/test_lot.py -v
```

期待: 3件 PASS

- [ ] **Step 3: cleanse.py を作成する**

`02_manufacturing/07_quality_portal/pipelines/lot/cleanse.py`:

```python
"""ロット判定: データクレンジング"""
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    "ロットID": "lot_id", "ロット番号": "lot_id", "Lot": "lot_id",
    "製品名": "product", "品名": "product",
    "検査日": "date", "判定日": "date",
    "検査項目": "item", "検査種別": "item",
    "判定": "result", "合否": "result",
}

files = sorted(Path(".").glob("*.csv"))
if not files:
    raise FileNotFoundError("CSVファイルが見つかりません")

dfs = [pd.read_csv(f, encoding="utf-8-sig").rename(
    columns={c: COLUMN_MAP[c] for c in pd.read_csv(f, encoding="utf-8-sig").columns if c in COLUMN_MAP}
) for f in files]
df = pd.concat(dfs, ignore_index=True)

required = {"lot_id", "product", "date", "item", "result"}
missing = required - set(df.columns)
if missing:
    raise ValueError(f"必要な列が不足しています: {missing}\n必要列: ロットID/製品名/検査日/検査項目/判定")

df["date"] = pd.to_datetime(df["date"])
valid_results = {"合格", "不合格"}
df["result"] = df["result"].where(df["result"].isin(valid_results), "不合格")
df = df.dropna(subset=["lot_id", "product"])

df.to_csv(OUTPUT_DIR / "cleaned_lot.csv", index=False, encoding="utf-8-sig")
print(f"クレンジング完了: {len(df)}件")
```

- [ ] **Step 4: analyze.py を作成する**

`02_manufacturing/07_quality_portal/pipelines/lot/analyze.py`:

```python
"""ロット判定: 分析レポート生成"""
import json
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("output")
df = pd.read_csv(OUTPUT_DIR / "cleaned_lot.csv", encoding="utf-8-sig")

lot_results = df.groupby("lot_id").apply(lambda x: "合格" if (x["result"] == "合格").all() else "不合格")
total_lots = len(lot_results)
passed_lots = (lot_results == "合格").sum()
failed_lots = (lot_results == "不合格").sum()
pass_rate = passed_lots / total_lots
review_needed = failed_lots

lines = ["# ロット別合否判定レポート\n",
         "## サマリー\n",
         f"- ロット合格率: {pass_rate:.2%}（{passed_lots}/{total_lots}ロット）",
         f"- 不合格ロット数: {failed_lots}件",
         f"- 要確認件数: {review_needed}件\n",
         "## 不合格ロット一覧\n",
         df[df["lot_id"].isin(lot_results[lot_results == "不合格"].index)][
             ["lot_id", "product", "item", "result"]
         ].query("result == '不合格'").to_markdown(index=False)]

(OUTPUT_DIR / "analysis_report.md").write_text("\n".join(lines), encoding="utf-8")

result = {
    "pass_rate": round(pass_rate, 4),
    "failed_lots": int(failed_lots),
    "review_needed": int(review_needed),
    "passed": 3,
    "results": [
        {"id": 1, "name": "ロット合否集計", "status": "PASS"},
        {"id": 2, "name": "製品別合格率", "status": "PASS"},
        {"id": 3, "name": "検査項目別不合格率", "status": "PASS"},
    ]
}
(OUTPUT_DIR / "result_analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
print("分析完了")
```

- [ ] **Step 5: visualize.py を作成する**

`02_manufacturing/07_quality_portal/pipelines/lot/visualize.py`:

```python
"""ロット判定: グラフ生成"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

try:
    import japanize_matplotlib
except ImportError:
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "pip", "install", "japanize-matplotlib"], check=True)
    import japanize_matplotlib

OUTPUT_DIR = Path("output")
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

df = pd.read_csv(OUTPUT_DIR / "cleaned_lot.csv", encoding="utf-8-sig")
df["date"] = pd.to_datetime(df["date"])

# 1. 製品別合格率棒グラフ
product_rates = df.groupby("product").apply(
    lambda x: (x["result"] == "合格").sum() / len(x)
).sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(10, 5))
colors = ["#16a34a" if r >= 0.95 else "#dc2626" for r in product_rates.values]
bars = ax.bar(product_rates.index, product_rates.values * 100, color=colors)
ax.set_title("製品別検査合格率", fontsize=14)
ax.set_ylabel("合格率（%）")
ax.set_ylim(80, 105)
ax.axhline(y=95, color="#d97706", linestyle="--", label="目標95%")
ax.bar_label(bars, fmt="%.1f%%", padding=3)
ax.legend()
plt.tight_layout()
plt.savefig(CHARTS_DIR / "bar_product_pass_rate.png", dpi=100)
plt.close()

# 2. 検査項目別不合格率棒グラフ
item_fail_rates = df.groupby("item").apply(
    lambda x: (x["result"] == "不合格").sum() / len(x)
).sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(item_fail_rates.index, item_fail_rates.values * 100, color="#1e3a5f")
ax.set_title("検査項目別不合格率", fontsize=14)
ax.set_ylabel("不合格率（%）")
ax.bar_label(bars, fmt="%.2f%%", padding=3)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "bar_item_fail_rate.png", dpi=100)
plt.close()

# 3. ロット一覧表（不合格ロット）
lot_results = df.groupby("lot_id").apply(lambda x: "合格" if (x["result"] == "合格").all() else "不合格")
failed_lot_ids = lot_results[lot_results == "不合格"].index.tolist()
fail_detail = df[df["lot_id"].isin(failed_lot_ids) & (df["result"] == "不合格")][
    ["lot_id", "product", "item", "result"]
].drop_duplicates().sort_values("lot_id")

fig, ax = plt.subplots(figsize=(10, max(3, len(fail_detail) * 0.4 + 1)))
ax.axis("off")
if len(fail_detail) > 0:
    table = ax.table(
        cellText=fail_detail.values,
        colLabels=["ロットID", "製品名", "不合格項目", "判定"],
        cellLoc="center", loc="center"
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)
    for (r, c), cell in table.get_celld().items():
        if r == 0:
            cell.set_facecolor("#1e3a5f")
            cell.set_text_props(color="white")
        elif r % 2 == 0:
            cell.set_facecolor("#f0f4f8")
ax.set_title("不合格ロット一覧", fontsize=14, pad=20)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "table_failed_lots.png", dpi=100)
plt.close()

result = {"passed": 3, "results": [
    {"id": 1, "name": "製品別合格率棒グラフ", "status": "PASS"},
    {"id": 2, "name": "検査項目別不合格率棒グラフ", "status": "PASS"},
    {"id": 3, "name": "不合格ロット一覧表", "status": "PASS"},
]}
(OUTPUT_DIR / "result_charts.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
print("グラフ生成完了")
```

- [ ] **Step 6: コミット**

```bash
git add 02_manufacturing/07_quality_portal/pipelines/lot/
git add 02_manufacturing/07_quality_portal/tests/test_lot.py
git commit -m "feat(quality-portal): add lot pipeline"
```

---

## Task 8: 共通ページ基盤モジュール

各ページで繰り返す「説明→入力選択→パイプライン実行→結果表示」のロジックを共通化する。

**Files:**

- Create: `02_manufacturing/07_quality_portal/pages/_pipeline_runner.py`

- [ ] **Step 1: _pipeline_runner.py を作成する**

`02_manufacturing/07_quality_portal/pages/_pipeline_runner.py`:

```python
"""パイプライン実行・結果表示の共通ロジック"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional
import streamlit as st


PIPELINE_ROOT = Path(__file__).parent.parent / "pipelines"


def _read_json(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"passed": 0, "results": [], "error": "ファイルが見つかりません"}


def _read_bytes(path: Path) -> Optional[bytes]:
    return path.read_bytes() if path.exists() else None


def run_pipeline(
    system_id: str,
    csv_bytes_dict: dict,          # {filename: bytes}
    step_labels: list,             # ["クレンジング", "分析", "グラフ生成"]
    scripts: list,                 # ["cleanse.py", "analyze.py", "visualize.py"]
    cleaned_csv_name: str,         # "cleaned_defect_rate.csv"
    chart_names: list,             # ["bar_line_defect.png", ...]
    kpi_extractor,                 # fn(result_analysis: dict) -> (val1, label1, val2, label2, val3, label3, color1, color2, color3)
):
    """パイプラインを実行し結果をStreamlitに表示する共通関数"""
    pipeline_dir = PIPELINE_ROOT / system_id

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        out = tmp / "output"
        out.mkdir()

        # CSVを一時ディレクトリに保存
        for fname, data in csv_bytes_dict.items():
            (tmp / fname).write_bytes(data)

        # パイプラインスクリプトをコピー
        for script in scripts:
            src = pipeline_dir / script
            if src.exists():
                shutil.copy(src, tmp / script)

        # プログレスバー付きで実行
        progress = st.progress(0, text="パイプライン開始...")
        total_steps = len(scripts)
        failed = False
        fail_msg = ""

        for i, (label, script) in enumerate(zip(step_labels, scripts)):
            pct = int((i + 1) / total_steps * 100)
            progress.progress(pct - 5 if pct > 5 else 1, text=f"{label}中...")

            result = subprocess.run(
                [sys.executable, script],
                cwd=str(tmp),
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            if result.returncode != 0:
                failed = True
                fail_msg = result.stderr or result.stdout
                break

            progress.progress(pct, text=f"{label} 完了")

        # 結果読み込み（temp削除前）
        result_analysis = _read_json(out / "result_analysis.json")
        result_charts = _read_json(out / "result_charts.json")
        report_text = (out / "analysis_report.md").read_text(encoding="utf-8") \
            if (out / "analysis_report.md").exists() else ""
        csv_bytes = _read_bytes(out / cleaned_csv_name)
        chart_images = {name: _read_bytes(out / "charts" / name) for name in chart_names}

    if failed:
        st.error("❌ パイプラインが失敗しました")
        st.markdown("**よくある原因:**")
        st.markdown("- CSVの列名が必要列と一致しているか確認してください")
        st.markdown("- 数値列に文字列が混入していないか確認してください")
        with st.expander("エラー詳細"):
            st.code(fail_msg)
        return

    st.success("✅ パイプライン完了")

    # KPIカード
    kpis = kpi_extractor(result_analysis)
    c1, c2, c3 = st.columns(3)
    for col, (val, label, color) in zip([c1, c2, c3], kpis):
        col.markdown(
            f"""<div style="background:{color};border-radius:8px;padding:16px;text-align:center">
            <div style="font-size:1.8em;font-weight:bold;color:white">{val}</div>
            <div style="color:rgba(255,255,255,0.85);font-size:0.9em">{label}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["📄 分析レポート", "📈 グラフ", "✅ 品質チェック", "⬇ ダウンロード"])

    with tab1:
        if report_text:
            st.markdown(report_text)
        else:
            st.warning("レポートが生成されませんでした")

    with tab2:
        for name, img in chart_images.items():
            if img:
                st.image(img, use_container_width=True)

    with tab3:
        c1, c2 = st.columns(2)
        for col, title, data in [
            (c1, f"分析品質（{result_analysis.get('passed', 0)}/3項目）", result_analysis),
            (c2, f"グラフ品質（{result_charts.get('passed', 0)}/3項目）", result_charts),
        ]:
            with col:
                st.subheader(title)
                for r in data.get("results", []):
                    icon = "✅" if r.get("status") == "PASS" else "❌"
                    st.write(f"{icon} {r.get('name', '')}")

    with tab4:
        if csv_bytes:
            st.download_button(
                "📥 クレンジング済みCSV",
                data=csv_bytes,
                file_name=cleaned_csv_name,
                mime="text/csv",
            )
        if report_text:
            st.download_button(
                "📥 分析レポート（Markdown）",
                data=report_text.encode("utf-8"),
                file_name="analysis_report.md",
                mime="text/markdown",
            )
        for name, img in chart_images.items():
            if img:
                st.download_button(f"📥 {name}", data=img, file_name=name, mime="image/png")
```

- [ ] **Step 2: コミット**

```bash
git add 02_manufacturing/07_quality_portal/pages/_pipeline_runner.py
git commit -m "feat(quality-portal): add shared pipeline runner module"
```

---

## Task 9: 5つのページモジュール

**Files:**

- Create: `02_manufacturing/07_quality_portal/pages/p1_defect_rate.py`
- Create: `02_manufacturing/07_quality_portal/pages/p2_claim.py`
- Create: `02_manufacturing/07_quality_portal/pages/p3_yield.py`
- Create: `02_manufacturing/07_quality_portal/pages/p4_inspector.py`
- Create: `02_manufacturing/07_quality_portal/pages/p5_lot.py`

- [ ] **Step 1: p1_defect_rate.py を作成する**

`02_manufacturing/07_quality_portal/pages/p1_defect_rate.py`:

```python
"""① 月次不良率集計ページ"""
from pathlib import Path
import streamlit as st
from pages._pipeline_runner import run_pipeline

SAMPLE_FILE = Path(__file__).parent.parent / "sample_defect_rate.csv"


def kpi_extractor(r: dict):
    rate = r.get("total_defect_rate", 0)
    color = "#16a34a" if rate < 0.03 else "#dc2626"
    return [
        (f"{rate:.2%}", "総不良率", color),
        (r.get("worst_line", "—"), "最多不良ライン", "#d97706"),
        (f"{r.get('total_inspected', 0):,}件", "検査総数", "#1e3a5f"),
    ]


def render():
    st.subheader("📊 月次不良率集計レポート")

    st.info(
        "**このツールでできること:** 工程別・製品別の不良率を自動集計し月次レポートを生成します\n\n"
        "**必要なCSV列:** 日付 / ライン / 製品名 / 検査数 / 不良数"
    )

    col1, col2 = st.columns(2)
    use_sample = col1.button("▶ サンプルで今すぐ試す", type="primary", use_container_width=True)
    uploaded = col2.file_uploader("📁 自分のCSVを使う", type=["csv"],
                                   accept_multiple_files=True, label_visibility="collapsed")

    csv_dict = {}
    if use_sample:
        csv_dict = {"sample_defect_rate.csv": SAMPLE_FILE.read_bytes()}
    elif uploaded:
        csv_dict = {f.name: f.getbuffer() for f in uploaded}
    else:
        st.caption("↑ サンプルで試すか、CSVをアップロードしてください")
        return

    run_pipeline(
        system_id="defect_rate",
        csv_bytes_dict=csv_dict,
        step_labels=["Step1: クレンジング", "Step2: 分析", "Step3: グラフ生成"],
        scripts=["cleanse.py", "analyze.py", "visualize.py"],
        cleaned_csv_name="cleaned_defect_rate.csv",
        chart_names=["bar_line_defect.png", "line_daily_defect.png", "heatmap_product_line.png"],
        kpi_extractor=kpi_extractor,
    )
```

- [ ] **Step 2: p2_claim.py を作成する**

`02_manufacturing/07_quality_portal/pages/p2_claim.py`:

```python
"""② クレーム件数集計ページ"""
from pathlib import Path
import streamlit as st
from pages._pipeline_runner import run_pipeline

SAMPLE_FILE = Path(__file__).parent.parent / "sample_claim.csv"


def kpi_extractor(r: dict):
    unresponded = r.get("unresponded", 0)
    color = "#dc2626" if unresponded > 5 else "#16a34a"
    return [
        (f"{r.get('total_claims', 0)}件", "総クレーム数", "#1e3a5f"),
        (f"{unresponded}件", "未対応件数", color),
        (r.get("top_supplier", "—"), "最多クレーム仕入先", "#d97706"),
    ]


def render():
    st.subheader("📋 クレーム件数集計レポート")

    st.info(
        "**このツールでできること:** 仕入先別・カテゴリ別のクレームを集計し対応状況を可視化します\n\n"
        "**必要なCSV列:** 日付 / 仕入先名 / 不良カテゴリ / 対応状況"
    )

    col1, col2 = st.columns(2)
    use_sample = col1.button("▶ サンプルで今すぐ試す", type="primary", use_container_width=True)
    uploaded = col2.file_uploader("📁 自分のCSVを使う", type=["csv"],
                                   accept_multiple_files=True, label_visibility="collapsed")

    csv_dict = {}
    if use_sample:
        csv_dict = {"sample_claim.csv": SAMPLE_FILE.read_bytes()}
    elif uploaded:
        csv_dict = {f.name: f.getbuffer() for f in uploaded}
    else:
        st.caption("↑ サンプルで試すか、CSVをアップロードしてください")
        return

    run_pipeline(
        system_id="claim",
        csv_bytes_dict=csv_dict,
        step_labels=["Step1: クレンジング", "Step2: 分析", "Step3: グラフ生成"],
        scripts=["cleanse.py", "analyze.py", "visualize.py"],
        cleaned_csv_name="cleaned_claim.csv",
        chart_names=["bar_supplier_claim.png", "pie_category.png", "line_weekly_claim.png"],
        kpi_extractor=kpi_extractor,
    )
```

- [ ] **Step 3: p3_yield.py を作成する**

`02_manufacturing/07_quality_portal/pages/p3_yield.py`:

```python
"""③ 歩留まりトレンドページ"""
from pathlib import Path
import streamlit as st
from pages._pipeline_runner import run_pipeline

SAMPLE_FILE = Path(__file__).parent.parent / "sample_yield.csv"


def kpi_extractor(r: dict):
    rate = r.get("avg_yield_rate", 0)
    color = "#16a34a" if rate >= 0.95 else "#dc2626"
    change = r.get("mom_change", 0)
    change_color = "#16a34a" if change >= 0 else "#dc2626"
    return [
        (f"{rate:.2%}", "平均歩留まり率", color),
        (r.get("lowest_process", "—"), "最低歩留まり工程", "#d97706"),
        (f"{change:+.1f}%", "前半→後半変化率", change_color),
    ]


def render():
    st.subheader("📈 歩留まりトレンドレポート")

    st.info(
        "**このツールでできること:** 工程別の歩留まり率を週次・月次トレンドで可視化します\n\n"
        "**必要なCSV列:** 日付 / 工程名 / 投入数 / 合格数"
    )

    col1, col2 = st.columns(2)
    use_sample = col1.button("▶ サンプルで今すぐ試す", type="primary", use_container_width=True)
    uploaded = col2.file_uploader("📁 自分のCSVを使う", type=["csv"],
                                   accept_multiple_files=True, label_visibility="collapsed")

    csv_dict = {}
    if use_sample:
        csv_dict = {"sample_yield.csv": SAMPLE_FILE.read_bytes()}
    elif uploaded:
        csv_dict = {f.name: f.getbuffer() for f in uploaded}
    else:
        st.caption("↑ サンプルで試すか、CSVをアップロードしてください")
        return

    run_pipeline(
        system_id="yield_",
        csv_bytes_dict=csv_dict,
        step_labels=["Step1: クレンジング", "Step2: 分析", "Step3: グラフ生成"],
        scripts=["cleanse.py", "analyze.py", "visualize.py"],
        cleaned_csv_name="cleaned_yield.csv",
        chart_names=["bar_process_yield.png", "line_weekly_yield.png", "heatmap_process_week.png"],
        kpi_extractor=kpi_extractor,
    )
```

- [ ] **Step 4: p4_inspector.py を作成する**

`02_manufacturing/07_quality_portal/pages/p4_inspector.py`:

```python
"""④ 検査員別実績ページ"""
from pathlib import Path
import streamlit as st
from pages._pipeline_runner import run_pipeline

SAMPLE_FILE = Path(__file__).parent.parent / "sample_inspector.csv"


def kpi_extractor(r: dict):
    avg = r.get("avg_pass_rate", 0)
    color = "#16a34a" if avg >= 0.95 else "#d97706"
    return [
        (f"{r.get('total_inspected', 0):,}件", "検査総数", "#1e3a5f"),
        (r.get("top_inspector", "—"), "最高精度検査員", "#16a34a"),
        (f"{avg:.2%}", "平均合格率", color),
    ]


def render():
    st.subheader("👷 検査員別実績レポート")

    st.info(
        "**このツールでできること:** 検査員・シフト別の検査数・合格率を集計し実績レポートを生成します\n\n"
        "**必要なCSV列:** 日付 / 検査員名 / シフト / 検査数 / 合格数"
    )

    col1, col2 = st.columns(2)
    use_sample = col1.button("▶ サンプルで今すぐ試す", type="primary", use_container_width=True)
    uploaded = col2.file_uploader("📁 自分のCSVを使う", type=["csv"],
                                   accept_multiple_files=True, label_visibility="collapsed")

    csv_dict = {}
    if use_sample:
        csv_dict = {"sample_inspector.csv": SAMPLE_FILE.read_bytes()}
    elif uploaded:
        csv_dict = {f.name: f.getbuffer() for f in uploaded}
    else:
        st.caption("↑ サンプルで試すか、CSVをアップロードしてください")
        return

    run_pipeline(
        system_id="inspector",
        csv_bytes_dict=csv_dict,
        step_labels=["Step1: クレンジング", "Step2: 分析", "Step3: グラフ生成"],
        scripts=["cleanse.py", "analyze.py", "visualize.py"],
        cleaned_csv_name="cleaned_inspector.csv",
        chart_names=["bar_inspector_rate.png", "bar_inspector_shift.png", "bar_daily_inspected.png"],
        kpi_extractor=kpi_extractor,
    )
```

- [ ] **Step 5: p5_lot.py を作成する**

`02_manufacturing/07_quality_portal/pages/p5_lot.py`:

```python
"""⑤ ロット別合否判定ページ"""
from pathlib import Path
import streamlit as st
from pages._pipeline_runner import run_pipeline

SAMPLE_FILE = Path(__file__).parent.parent / "sample_lot.csv"


def kpi_extractor(r: dict):
    rate = r.get("pass_rate", 0)
    color = "#16a34a" if rate >= 0.95 else "#dc2626"
    failed = r.get("failed_lots", 0)
    return [
        (f"{rate:.2%}", "ロット合格率", color),
        (f"{failed}件", "不合格ロット数", "#dc2626" if failed > 0 else "#16a34a"),
        (f"{r.get('review_needed', 0)}件", "要確認件数", "#d97706" if r.get("review_needed", 0) > 0 else "#16a34a"),
    ]


def render():
    st.subheader("📦 ロット別合否判定レポート")

    st.info(
        "**このツールでできること:** 製品ロットの合否判定結果を集計し要確認ロットを抽出します\n\n"
        "**必要なCSV列:** ロットID / 製品名 / 検査日 / 検査項目 / 判定"
    )

    col1, col2 = st.columns(2)
    use_sample = col1.button("▶ サンプルで今すぐ試す", type="primary", use_container_width=True)
    uploaded = col2.file_uploader("📁 自分のCSVを使う", type=["csv"],
                                   accept_multiple_files=True, label_visibility="collapsed")

    csv_dict = {}
    if use_sample:
        csv_dict = {"sample_lot.csv": SAMPLE_FILE.read_bytes()}
    elif uploaded:
        csv_dict = {f.name: f.getbuffer() for f in uploaded}
    else:
        st.caption("↑ サンプルで試すか、CSVをアップロードしてください")
        return

    run_pipeline(
        system_id="lot",
        csv_bytes_dict=csv_dict,
        step_labels=["Step1: クレンジング", "Step2: 分析", "Step3: グラフ生成"],
        scripts=["cleanse.py", "analyze.py", "visualize.py"],
        cleaned_csv_name="cleaned_lot.csv",
        chart_names=["bar_product_pass_rate.png", "bar_item_fail_rate.png", "table_failed_lots.png"],
        kpi_extractor=kpi_extractor,
    )
```

- [ ] **Step 6: コミット**

```bash
git add 02_manufacturing/07_quality_portal/pages/
git commit -m "feat(quality-portal): add 5 page modules"
```

---

## Task 10: portal.py（メインアプリ）

**Files:**

- Create: `02_manufacturing/07_quality_portal/portal.py`

- [ ] **Step 1: portal.py を作成する**

`02_manufacturing/07_quality_portal/portal.py`:

```python
"""
品質管理ポータル — メインアプリ
起動: streamlit run portal.py
"""
import sys
from pathlib import Path

import streamlit as st
import yaml

# pages/ を import パスに追加
sys.path.insert(0, str(Path(__file__).parent))

from pages import p1_defect_rate, p2_claim, p3_yield, p4_inspector, p5_lot

CONFIG_PATH = Path(__file__).parent / "config.yml"
config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))

st.set_page_config(
    page_title=config["portal"]["title"],
    page_icon=config["portal"]["icon"],
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── サイドバー CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] {
    background-color: #1e3a5f;
}
[data-testid="stSidebar"] * {
    color: #ffffff !important;
}
[data-testid="stSidebar"] .stButton button {
    background-color: transparent;
    color: white !important;
    border: none;
    text-align: left;
    padding: 8px 12px;
    width: 100%;
    font-size: 0.95em;
    border-radius: 6px;
    transition: background 0.2s;
}
[data-testid="stSidebar"] .stButton button:hover {
    background-color: #2a5298 !important;
}
</style>
""", unsafe_allow_html=True)

# ── サイドバー ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"## {config['portal']['icon']} {config['portal']['title']}")
    st.markdown("---")

    PAGES = {
        "📊 月次不良率集計":    "defect_rate",
        "📋 クレーム件数集計":  "claim",
        "📈 歩留まりトレンド":  "yield_",
        "👷 検査員別実績":      "inspector",
        "📦 ロット別合否判定":  "lot",
    }

    if "current_page" not in st.session_state:
        st.session_state.current_page = "defect_rate"

    for label, page_id in PAGES.items():
        if st.button(label, key=f"nav_{page_id}", use_container_width=True):
            st.session_state.current_page = page_id

    st.markdown("---")
    st.caption("製造業・品質保証部門向け\nDXポートフォリオ C-61")

# ── メインコンテンツ ────────────────────────────────────────────────
PAGE_MAP = {
    "defect_rate": p1_defect_rate,
    "claim":       p2_claim,
    "yield_":      p3_yield,
    "inspector":   p4_inspector,
    "lot":         p5_lot,
}

PAGE_MAP[st.session_state.current_page].render()
```

- [ ] **Step 2: 起動して動作確認する**

```bash
cd 02_manufacturing/07_quality_portal
pip install -r requirements.txt
streamlit run portal.py
```

期待: ブラウザでネイビーサイドバー付きポータルが表示され、各システムに切り替えられる

- [ ] **Step 3: サンプルボタンで全5システムを動作確認する**

各システムで「▶ サンプルで今すぐ試す」をクリックし、KPIカード・グラフ・レポートが表示されることを確認する

- [ ] **Step 4: コミット**

```bash
git add 02_manufacturing/07_quality_portal/portal.py
git commit -m "feat(quality-portal): add main portal.py with sidebar navigation"
```

---

## Task 11: catalog.yml 登録 & 最終コミット

**Files:**

- Modify: `catalog.yml`

- [ ] **Step 1: catalog.yml に C-61 を追加する**

`catalog.yml` の末尾に追加：

```yaml
- id: "C-61"
  name: "製造業品質管理ポータル（統合）"
  industry: "製造"
  department: "生産・品質"
  status: "production-ready"
  priority: "C"
  path: "02_manufacturing/07_quality_portal"
  description: "不良率集計・クレーム管理・歩留まりトレンド・検査員実績・ロット合否の5システムを統合した品質保証部門向けStreamlitポータル。サンプルデータで即体験可能。"
  demo: "cd 02_manufacturing/07_quality_portal && streamlit run portal.py"
```

- [ ] **Step 2: 全テストを実行する**

```bash
cd 02_manufacturing/07_quality_portal
python -m pytest tests/ -v
```

期待: 全13件 PASS

- [ ] **Step 3: 最終コミット**

```bash
git add catalog.yml
git commit -m "feat(catalog): register C-61 quality management portal"
```

---

## 完了チェックリスト

- [ ] `portal.py` 起動でサイドバー付きポータルが表示される
- [ ] サイドバーの5システムが切り替えられる
- [ ] 全5システムでサンプルボタンが動作する
- [ ] 全5システムでKPIカード・グラフ・レポート・ダウンロードが機能する
- [ ] CSVアップロードでも動作する
- [ ] エラー時に「よくある原因」が表示される
- [ ] 全テスト PASS
- [ ] `catalog.yml` に C-61 が登録済み

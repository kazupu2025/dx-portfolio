# C-94 ロット完全トレーサビリティ

**System ID:** `lot_traceability`

## Metadata

| Key | Value |
|-----|-------|
| name | ロット完全トレーサビリティ（networkx グラフ可視化） |
| industry | 製造 |
| department | 品質保証 |
| status | **production-ready** |
| path | `02_manufacturing/40_lot_traceability` |

## Overview

原材料 → 工程 → 出荷先 の関係を CSV で定義し、networkx 有向グラフで**双方向トレーサビリティ**を実現。
ロット番号での絞り込み追跡が可能。ノード数 ≤ 10 → "good" の verdict でサプライチェーン複雑度を管理。
Plotly Scatter グラフで階層レイアウトの視覚的なサプライチェーン図を生成。

## Components

- **analyze.py** — networkx グラフ構築 + 複雑度 verdict 判定（7キー出力）
- **visualize.py** — Plotly グラフ可視化（階層レイアウト） + ロット別経路テーブル
- **app.py** — Streamlit UI（グラフ表示 + CSV upload + DB連携）
- **sample_data.py** — 3ロット × 12ノード デモデータ
- **tests/test_analyze.py** — TDD：8テスト all PASS

## Test Results

```
8 passed
  ✓ test_verdict_good         — n_nodes ≤ 10 → "good"
  ✓ test_verdict_warning      — n_nodes 11-20 → "warning"
  ✓ test_verdict_alert        — n_nodes > 20 → "alert"
  ✓ test_n_nodes              — 4 ノード（原材料A/工程1/工程2/得意先X）
  ✓ test_n_edges              — 3 エッジ
  ✓ test_n_lots               — 2 ロット（L001, L002）
  ✓ test_material_nodes       — 原材料A 検出
  ✓ test_missing_column_raises — 必須列欠落時 ValueError
```

## Data Schema

**Input CSV（Long形式）**

| Column | Type | Example |
|--------|------|---------|
| from_node | str | "鋼材A" |
| to_node | str | "切削工程" |
| edge_type | str | "材料→工程" |
| lot_id | str | "L001" |
| quantity | float | 100.0 |

**analyze.py Output（7キー）**

```python
{
    "G":                  nx.DiGraph,        # networkx 有向グラフ
    "n_nodes":            int,               # ノード総数
    "n_edges":            int,               # エッジ総数
    "n_lots":             int,               # ユニーク lot_id 数
    "material_nodes":     list[str],         # edge_type="材料→工程" の from_node
    "destination_nodes":  list[str],         # edge_type="工程→出荷" の to_node
    "verdict":            str,               # "good" / "warning" / "alert"
}
```

## DB Metric

- **system_id:** `lot_traceability`
- **metric:** `n_lots`（管理ロット数）
- **CARD:**
  ```python
  {"system_id": "lot_traceability", "metric": "n_lots", "title": "管理ロット数", "fmt": lambda v: f"{int(v)}件"}
  ```

## Usage

```bash
# Streamlit で起動
streamlit run 02_manufacturing/40_lot_traceability/app.py

# テスト実行
pytest 02_manufacturing/40_lot_traceability/tests/ -v
```

## Created

2026-06-23 — C-94 実装開始 / TDD 完成 / production-ready

# 品質コスト明細集計（4分類）設計仕様書

**作成日:** 2026-06-22
**システムID:** C-75
**難易度:** ★★★
**カテゴリ:** 製造業 / 品質保証（QA）

---

## 1. 概要

月次の品質コスト明細（4分類：予防・評価・内部損失・外部損失）を CSV でアップロードし、
損失コスト比率（内部損失＋外部損失 / 全体）を自動算出して月次トレンドと分類別内訳を可視化する。
損失コスト比率 ≤ 30% → "good" の明快な verdict 設計で、結果を quality.db に書き込んで C-63 統合ダッシュボードに連携する。

---

## 2. 入力データ仕様

### CSV フォーマット（Long 3列・1行=1月×1分類）

```csv
month,category,amount
2024-01,予防コスト,150000
2024-01,評価コスト,200000
2024-01,内部損失コスト,180000
2024-01,外部損失コスト,120000
2024-02,予防コスト,160000
```

- `month`: 年月（YYYY-MM 形式）
- `category`: 分類（予防コスト / 評価コスト / 内部損失コスト / 外部損失コスト）
- `amount`: 金額（0以上の整数）
- 最低構成: n ≥ 1

---

## 3. ファイル構成

```text
02_manufacturing/21_quality_cost/
├── app.py           # Streamlit UI + DB 統合
├── analyze.py       # コスト集計ロジック（純粋関数）
├── visualize.py     # Plotly 積み上げ棒グラフ + 分類別横棒
├── sample_data.py   # デモ CSV 生成（6ヶ月 × 4分類）
├── STATUS.md
└── tests/
    ├── __init__.py
    └── test_analyze.py   # 8テスト（TDD）
```

---

## 4. データフロー

```text
CSV（month, category, amount）
  └─ app.py
       └─ analyze.py: run_analysis() → コスト集計 + verdict
            ├─ visualize.py: monthly_cost_chart() + category_bar_chart()
            └─ _common/db_writer.py: write_kpi("quality_cost", ..., "failure_ratio", ratio, verdict)
                  └─ C-63 dashboard: quality_cost カード追加
```

---

## 5. analyze.py — 計算ロジック

### 必須列

```python
REQUIRED_COLS = ["month", "category", "amount"]
```

### 処理フロー

1. 必須列の存在確認 → なければ ValueError
2. `amount` を `pd.to_numeric(errors="coerce")` で変換 + NaN 行 `dropna()`
3. `amount < 0` の行を除外（0円は有効）
4. n < 1 で ValueError（"有効なデータがありません"）
5. `total_cost = int(df["amount"].sum())`
6. `n_months = df["month"].nunique()`
7. `avg_monthly_cost = total_cost / n_months`
8. `cost_by_category`: category ごとの amount 合計 dict
9. `dominant_category`: amount 合計が最大の category
10. `failure_ratio`: （内部損失コスト + 外部損失コスト）/ total_cost × 100
11. verdict 判定

### 損失コスト比率の計算

```python
FAILURE_CATEGORIES = ["内部損失コスト", "外部損失コスト"]

failure_amount = sum(
    cost_by_category.get(cat, 0) for cat in FAILURE_CATEGORIES
)
failure_ratio = failure_amount / total_cost * 100
```

### verdict 基準

| 条件 | verdict | 意味 |
|------|---------|------|
| failure_ratio ≤ 30.0 | `"good"` | 品質管理良好 |
| failure_ratio ≤ 50.0 | `"warning"` | 要注意 |
| failure_ratio > 50.0 | `"alert"` | 要改善 |

### シグネチャ

```python
def run_analysis(df: pd.DataFrame) -> dict:
```

### 出力 dict（7キー）

```python
{
    "result_df":          pd.DataFrame,  # クレンジング済みデータ
    "total_cost":         int,           # 全期間コスト合計
    "avg_monthly_cost":   float,         # 月次平均コスト
    "cost_by_category":   dict,          # {category: int} 分類別合計
    "dominant_category":  str,           # 最大コスト分類
    "failure_ratio":      float,         # 損失コスト比率（%）
    "verdict":            str,           # "good" | "warning" | "alert"
}
```

### エラー

```python
if missing := [c for c in REQUIRED_COLS if c not in df.columns]:
    raise ValueError(f"必須列が不足しています: {', '.join(missing)}")
if len(data) < 1:
    raise ValueError("有効なデータがありません。")
```

---

## 6. visualize.py — Plotly チャート

### monthly_cost_chart(result_df) → go.Figure

- 月次 × 4分類の積み上げ棒グラフ（`barmode="stack"`）
- x 軸: month / トレース: category（4分類）
- pivot: `result_df.groupby(["month","category"])["amount"].sum().reset_index().pivot(index="month", columns="category", values="amount").reindex(sorted_months)`
- カラー: 予防コスト=#16a34a, 評価コスト=#0891b2, 内部損失コスト=#d97706, 外部損失コスト=#dc2626
- タイトル: "品質コスト月次推移（4分類）"
- 高さ: 380px、BG: `#f5f7fa`

### category_bar_chart(result_df) → go.Figure

- 分類別の総コスト横棒グラフ（`orientation="h"`）
- 件数降順ソート（多い順が上に表示）
- 棒の色: 予防=#16a34a, 評価=#0891b2, 内部損失=#d97706, 外部損失=#dc2626
- テキスト: 金額（¥XXX,XXX）を棒の外側に表示
- タイトル: "分類別 品質コスト合計"
- 高さ: 320px、BG: `#f5f7fa`

カラーテーマ（統一）:
- Navy: `#1e3a5f`, Alert: `#dc2626`, Good: `#16a34a`, Warning: `#d97706`, Info: `#0891b2`, BG: `#f5f7fa`

---

## 7. sample_data.py — デモ用サンプルデータ

```
6ヶ月（2024-01〜2024-06）× 4分類 = 24行

設定:
- 予防コスト: 月 ≈ 150,000円（低め）
- 評価コスト: 月 ≈ 200,000円（中程度）
- 内部損失コスト: 月 ≈ 180,000円（中程度）
- 外部損失コスト: 月 ≈ 120,000円（中程度）
→ total ≈ 650,000円/月
→ failure_ratio ≈ (180,000+120,000)/650,000 ≈ 46% → verdict = "warning"
dominant_category: 評価コスト
```

列構成: `month`, `category`, `amount`

---

## 8. app.py — UI レイアウト

```text
┌─────────────────┬──────────────────────────────────────────────┐
│ ⚙ 設定          │ KPI（4列）                                    │
│ CSV upload      │  月次平均コスト | 最大分類 | 損失比率 | verdict │
│ [サンプルデータ] │                                              │
│ [▶ 分析実行]   │  積み上げ棒グラフ | 分類別横棒グラフ            │
└─────────────────┴──────────────────────────────────────────────┘
```

### KPI 4列

| 列 | 表示内容 |
|----|---------|
| c1 | 月次平均コスト（`¥{avg_monthly_cost:,.0f}`）|
| c2 | 最大コスト分類（`{dominant_category}`）|
| c3 | 損失コスト比率（`{failure_ratio:.1f}%`）|
| c4 | verdict カード（good/warning/alert 色付き）|

### verdict ラベル

```python
_LABEL = {"good": "品質管理良好", "warning": "要注意", "alert": "要改善"}
_COLOR = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
```

### 状態管理

- `st.session_state["df"]` でデータ保持
- `st.session_state["result"]` で分析結果保持

### エラーハンドリング

- 列不足・データ空 → `st.error()` + `st.stop()`
- DB 書き込み失敗 → `except Exception: st.caption(...)` でアプリ継続

---

## 9. DB 統合

```python
init_db()
uid = write_upload("quality_cost", filename, row_count)
write_kpi(
    uid, "quality_cost",
    datetime.now().strftime("%Y-%m"),
    "failure_ratio", float(failure_ratio), verdict,
)
```

### C-63 ダッシュボード — CARDS 追加

```python
{"system_id": "quality_cost", "metric": "failure_ratio",
 "title": "損失コスト比率", "fmt": lambda v: f"{v:.1f}%"}
```

---

## 10. テスト方針（test_analyze.py）

8テスト（TDD）:

| テスト名 | 内容 |
|---------|------|
| `test_verdict_good` | failure_ratio = 30.0 → "good"（境界値）|
| `test_verdict_warning` | failure_ratio = 40.0 → "warning" |
| `test_verdict_alert` | failure_ratio = 60.0 → "alert" |
| `test_verdict_warning_upper_boundary` | failure_ratio = 50.0 → "warning"（上限境界値）|
| `test_total_cost` | amount 合計の正確性 |
| `test_cost_by_category` | 分類別集計の正確性 |
| `test_dominant_category` | 最大コスト分類の特定 |
| `test_missing_column_raises` | 必須列なし → ValueError |

---

## 11. catalog.yml エントリ

```yaml
- id: "C-75"
  name: "品質コスト明細集計（4分類）"
  industry: "製造"
  department: "品質保証"
  difficulty: "★★★"
  status: "production-ready"
  priority: "A"
  path: "02_manufacturing/21_quality_cost"
  demo: "streamlit run 02_manufacturing/21_quality_cost/app.py"
  description: |
    月次の品質コスト明細（予防・評価・内部損失・外部損失）を CSV でアップロードし、
    損失コスト比率を自動算出。損失比率 ≤ 30% → "good" の明快な verdict 設計。
    積み上げ棒グラフと分類別横棒グラフで改善ポイントを可視化。
```

---

## 12. スコープ外（将来対応）

- 売上高対品質コスト比率（品質コスト率）の算出
- 業界ベンチマーク比較
- 改善活動（CAPA）との連携

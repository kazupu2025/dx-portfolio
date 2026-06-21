# 仕入先品質複合スコアリング 設計仕様書

**作成日:** 2026-06-21
**システムID:** C-68
**難易度:** ★★☆
**カテゴリ:** 製造業 / 品質管理（QA）

---

## 1. 概要

仕入先ごとの品質指標（不良率・納期遵守率・価格偏差）を CSV でアップロードし、
固定重み付き合成スコアを自動計算して仕入先をランク付けする。
合成スコア ≥ 80 → "good"（優良）という明快な verdict 設計で、
結果を quality.db に書き込んで C-63 統合ダッシュボードに連携する。

---

## 2. 入力データ仕様

### CSV フォーマット（Wide 4列・1行=1仕入先）

```csv
supplier_id,defect_rate,delivery_rate,price_variance
SUP-A,1.2,95.0,3.0
SUP-B,3.5,88.0,8.0
SUP-C,0.8,98.0,1.5
SUP-D,5.0,82.0,12.0
SUP-E,2.1,91.0,4.5
```

- `supplier_id`: 仕入先識別子（文字列）
- `defect_rate`: 不良率（%）— 低いほど良い
- `delivery_rate`: 納期遵守率（%）— 高いほど良い
- `price_variance`: 価格偏差（%）— 低いほど良い
- 最低構成: n ≥ 1（1仕入先でも動作）

---

## 3. ファイル構成

```text
02_manufacturing/17_supplier_scoring/
├── app.py           # Streamlit UI + DB統合
├── analyze.py       # スコア計算ロジック（純粋関数）
├── visualize.py     # Plotly 合成スコア棒グラフ + 指標内訳グラフ
├── sample_data.py   # デモCSV生成（5仕入先）
├── STATUS.md
└── tests/
    ├── __init__.py
    └── test_analyze.py   # 8テスト（TDD）
```

---

## 4. データフロー

```text
CSV（supplier_id + defect_rate + delivery_rate + price_variance）
  └─ app.py
       └─ analyze.py: run_analysis() → 仕入先別スコア + verdict
            ├─ visualize.py: score_bar_chart() + breakdown_chart()
            └─ _common/db_writer.py: write_kpi("supplier_scoring", ..., "avg_score", avg_score, verdict)
                  └─ C-63 dashboard: supplier_scoring カード追加
```

---

## 5. analyze.py — スコア計算ロジック

### 固定重みと指標変換

```python
WEIGHTS = {"defect_rate": 0.5, "delivery_rate": 0.3, "price_variance": 0.2}

def _score_defect(v: float) -> float:
    return max(0.0, 100.0 - v * 10.0)   # 不良率 1% → 90点、10%以上 → 0点

def _score_delivery(v: float) -> float:
    return float(min(100.0, v))          # 納期遵守率 95% → 95点（上限100）

def _score_price(v: float) -> float:
    return max(0.0, 100.0 - v * 5.0)    # 価格偏差 3% → 85点、20%以上 → 0点
```

### シグネチャ

```python
def run_analysis(df: pd.DataFrame) -> dict:
```

### 処理フロー

1. 必須列（`supplier_id`, `defect_rate`, `delivery_rate`, `price_variance`）の存在確認 → なければ ValueError
2. 数値列を `pd.to_numeric(errors="coerce")` で変換 + NaN行 `dropna()`
3. n < 1 で ValueError（"有効なデータがありません"）
4. 各指標を 0〜100 スコアに変換（`_score_defect`, `_score_delivery`, `_score_price`）
5. 合成スコア = `defect_score × 0.5 + delivery_score × 0.3 + price_score × 0.2`
6. 仕入先ごとに verdict 判定
7. 全仕入先の平均スコアでシステム全体の verdict を決定

### verdict 基準（仕入先ごと & システム全体共通）

| 条件 | verdict | 意味 |
|------|---------|------|
| composite_score ≥ 80 | `"good"` | 優良仕入先 |
| composite_score ≥ 60 | `"warning"` | 要改善 |
| composite_score < 60 | `"alert"` | 取引見直し検討 |

システム全体 verdict は `avg_score`（全仕入先平均合成スコア）で判定。

### 出力 dict（6キー）

```python
{
    "scored_df":      pd.DataFrame,  # supplier_id + defect_score + delivery_score +
                                     # price_score + composite_score + verdict 列を含む
    "avg_score":      float,         # 全仕入先平均合成スコア
    "best_supplier":  str,           # 最高スコアの仕入先 supplier_id
    "worst_supplier": str,           # 最低スコアの仕入先 supplier_id
    "n_suppliers":    int,
    "verdict":        str,           # avg_score ベースの "good"|"warning"|"alert"
}
```

### エラー

```python
REQUIRED_COLS = ["supplier_id", "defect_rate", "delivery_rate", "price_variance"]

# 列不足
if missing := [c for c in REQUIRED_COLS if c not in df.columns]:
    raise ValueError(f"必須列が不足しています: {', '.join(missing)}")
# データ空
if len(data) < 1:
    raise ValueError("有効なデータがありません。")
```

---

## 6. visualize.py — Plotly チャート

### score_bar_chart(scored_df) → go.Figure

- `go.Bar(orientation="h")` — 横棒グラフ
- composite_score 降順ソート（高スコアを上に）
- 棒の色: verdict ごとに good=#16a34a / warning=#d97706 / alert=#dc2626
- しきい値縦線: `add_vline(x=80, line_dash="dash", line_color="#1e3a5f")` + `add_vline(x=60, ...)`
- タイトル: "仕入先別 合成スコア"
- 高さ: 350px

### breakdown_chart(scored_df) → go.Figure

- グループ棒グラフ（`barmode="group"`）
- トレース × 3:
  - defect_score: color `#dc2626`、name "不良スコア"
  - delivery_score: color `#16a34a`、name "納期スコア"
  - price_score: color `#1e3a5f`、name "価格スコア"
- x軸: supplier_id、y軸: スコア（0〜100）
- タイトル: "指標別スコア内訳"
- 高さ: 350px

カラーテーマ（C-61〜C-71 統一）:
- Navy: `#1e3a5f`, Alert: `#dc2626`, Good: `#16a34a`, Warning: `#d97706`, BG: `#f5f7fa`

---

## 7. sample_data.py — デモ用サンプルデータ

```python
"""
5仕入先（SUP-A〜SUP-E）の品質指標

設定:
- SUP-A: 優良（composite ≈ 87 → "good"）
- SUP-B: 普通（composite ≈ 67 → "warning"）
- SUP-C: 最優良（composite ≈ 93 → "good"）
- SUP-D: 要改善（composite ≈ 48 → "alert"）
- SUP-E: 普通（composite ≈ 72 → "warning"）
"""
```

列構成: `supplier_id`, `defect_rate`, `delivery_rate`, `price_variance`

---

## 8. app.py — UI レイアウト

```text
┌─────────────────┬──────────────────────────────────────────────┐
│ ⚙ 設定          │ KPI（4列）                                    │
│ [サンプルデータ] │  仕入先数 | 平均スコア | 最優良仕入先 | verdict  │
│ CSV upload      │                                              │
│ [▶ 分析実行]   │  合成スコア横棒グラフ   │  指標別内訳グラフ      │
│               　│  仕入先別スコアテーブル（verdict カラー付き）   │
└─────────────────┴──────────────────────────────────────────────┘
```

### KPI 4列

| 列 | 表示内容 |
|----|---------|
| c1 | 仕入先数（`{n_suppliers}社`）|
| c2 | 平均合成スコア（`{avg_score:.1f}点`）|
| c3 | 最優良仕入先（`{best_supplier}`、delta=スコア）|
| c4 | verdict カード（good/warning/alert 色付き）|

### verdict ラベル

```python
_LABEL = {"good": "優良仕入先多数", "warning": "改善余地あり", "alert": "取引見直し検討"}
_COLOR = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
```

### テーブル表示

`scored_df` の `supplier_id`, `defect_rate`, `delivery_rate`, `price_variance`,
`composite_score`, `verdict` 列を `st.dataframe` で表示。

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
uid = write_upload("supplier_scoring", filename, row_count)
write_kpi(uid, "supplier_scoring", datetime.now().strftime("%Y-%m"), "avg_score", avg_score, verdict)
```

### C-63 ダッシュボード — CARDS 追加

```python
{"system_id": "supplier_scoring", "metric": "avg_score",
 "title": "仕入先平均スコア", "fmt": lambda v: f"{v:.1f}点"}
```

---

## 10. テスト方針（test_analyze.py）

8テスト（TDD）:

| テスト名 | 内容 |
|---------|------|
| test_verdict_good | avg_score ≥ 80 → "good" |
| test_verdict_warning | 60 ≤ avg_score < 80 → "warning" |
| test_verdict_alert | avg_score < 60 → "alert" |
| test_score_defect_conversion | defect_rate=1.0 → defect_score=90.0 |
| test_score_delivery_conversion | delivery_rate=95.0 → delivery_score=95.0 |
| test_score_price_conversion | price_variance=10.0 → price_score=50.0 |
| test_output_keys | 全6キーが揃っていること |
| test_missing_column_raises | 必須列なし → ValueError |

---

## 11. catalog.yml エントリ

```yaml
- id: "C-68"
  name: "仕入先品質複合スコアリング — 重み付き合成スコア × 仕入先ランク"
  industry: "製造"
  department: "購買・品質"
  difficulty: "★★☆"
  status: "production-ready"
  priority: "B"
  path: "02_manufacturing/17_supplier_scoring"
  demo: "streamlit run 02_manufacturing/17_supplier_scoring/app.py"
  description: |
    仕入先ごとの品質指標（不良率・納期遵守率・価格偏差）を重み付き合成スコアに変換してランク付け。
    固定重み（不良率50%・納期30%・価格20%）でシンプルに計算し、スコア≥80→"good"で優良判定。
    横棒グラフで仕入先ランキング、指標別内訳グラフで改善ポイントを可視化。
```

---

## 12. スコープ外（将来対応）

- 重みの UI スライダー調整
- 月次トレンド比較（仕入先スコアの推移）
- 複数カテゴリ（A/B/C 評価）への分類
- 監査スコア・クレーム対応速度の追加指標

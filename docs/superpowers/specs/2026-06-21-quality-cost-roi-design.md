# 品質コストROI分析 設計仕様書

**作成日:** 2026-06-21
**システムID:** C-71
**難易度:** ★★☆
**カテゴリ:** 製造業 / 品質管理（QA）

---

## 1. 概要

月次の品質コスト（予防・評価・失敗）を CSV でアップロードし、
PAF モデルに基づく ROI（改善効果 / 投資額）を自動計算する。
月次比較で失敗コストの削減額が投資額を上回るか判定し、
結果を quality.db に書き込んで C-63 統合ダッシュボードに連携する。

---

## 2. 入力データ仕様

### CSV フォーマット（Wide 4列）

```csv
month,prevention_cost,appraisal_cost,failure_cost
2024-01,500000,300000,1200000
2024-02,600000,280000,950000
2024-03,620000,290000,800000
```

- `month`: 年月文字列（YYYY-MM など）— ソートキーとして使用
- `prevention_cost`: 予防コスト（教育・工程改善など）
- `appraisal_cost`: 評価コスト（検査・監査など）
- `failure_cost`: 失敗コスト（不良・手直し・クレームなど、内部/外部合算）
- 最低構成: n ≥ 1（1行でも動作、フォールバックあり）
- ROI 計算には n ≥ 2 が必要

---

## 3. ファイル構成

```text
02_manufacturing/16_quality_cost_roi/
├── app.py           # Streamlit UI + DB統合
├── analyze.py       # ROI計算ロジック（純粋関数）
├── visualize.py     # Plotly 積み上げ棒グラフ + ROI折れ線グラフ
├── sample_data.py   # デモCSV生成（12ヶ月、改善傾向あり）
├── STATUS.md
└── tests/
    ├── __init__.py
    └── test_analyze.py   # 8テスト（TDD）
```

---

## 4. データフロー

```text
CSV（month, prevention_cost, appraisal_cost, failure_cost）
  └─ app.py
       └─ analyze.py: run_analysis() → ROI時系列 + verdict
            ├─ visualize.py: cost_bar_chart() + roi_line_chart()
            └─ _common/db_writer.py: write_kpi("quality_cost_roi", ..., "roi", value, verdict)
                  └─ C-63 dashboard: quality_cost_roi カード追加
```

---

## 5. analyze.py — ROI計算ロジック

### シグネチャ

```python
def run_analysis(df: pd.DataFrame) -> dict:
```

### 処理フロー

1. 必須列（`month`, `prevention_cost`, `appraisal_cost`, `failure_cost`）の存在確認 → なければ ValueError
2. 数値列を `pd.to_numeric(errors="coerce")` で変換 + NaN行 `dropna()`
3. `month` 列で昇順ソート
4. n < 1 で ValueError（"データが空です"）
5. n ≥ 2: 月次ROI計算
6. n == 1: failure_ratio フォールバック

### ROI計算（n ≥ 2）

```python
# 各月のROI = (前月failure - 当月failure) / (当月prevention + appraisal)
roi_series = []
for i in range(1, len(df)):
    delta  = df["failure_cost"].iloc[i-1] - df["failure_cost"].iloc[i]  # 削減額（正=改善）
    invest = df["prevention_cost"].iloc[i] + df["appraisal_cost"].iloc[i]
    roi_series.append(delta / invest if invest > 0 else 0.0)
latest_roi = roi_series[-1]
```

### フォールバック（n == 1）

```python
total_qc      = prevention + appraisal + failure
failure_ratio = failure / total_qc if total_qc > 0 else 0.0
# failure_ratio < 0.3  → "good"
# failure_ratio < 0.5  → "warning"
# failure_ratio ≥ 0.5  → "alert"
```

### verdict 基準

**n ≥ 2（ROI モード）:**

| 条件 | verdict | 意味 |
|------|---------|------|
| latest_roi > 1.0 | `"good"` | 投資回収済み（削減額 > 投資額）|
| latest_roi > 0.0 | `"warning"` | 改善中（未回収）|
| latest_roi ≤ 0.0 | `"alert"` | 要投資見直し（悪化または横ばい）|

**n == 1（failure_ratio モード）:**

| 条件 | verdict | 意味 |
|------|---------|------|
| failure_ratio < 0.3 | `"good"` | 失敗コスト比率が低い |
| failure_ratio < 0.5 | `"warning"` | 要監視 |
| failure_ratio ≥ 0.5 | `"alert"` | 失敗コストが支配的 |

### 出力 dict（8キー）

```python
{
    "roi_series":       list[float],   # ROI時系列（n-1個、n==1時は空リスト）
    "latest_roi":       float | None,  # 最新月ROI（n==1時はNone）
    "failure_ratio":    float,         # 最新月 failure/(P+A+F)
    "total_prevention": float,         # 累計予防コスト
    "total_appraisal":  float,         # 累計評価コスト
    "total_failure":    float,         # 累計失敗コスト
    "n_months":         int,
    "verdict":          str,           # "good" | "warning" | "alert"
}
```

### エラー

```python
# 列不足
if not all(col in df.columns for col in REQUIRED_COLS):
    raise ValueError("必須列が不足しています: month, prevention_cost, appraisal_cost, failure_cost")
# データ空
if len(df) < 1:
    raise ValueError("有効なデータがありません。")
```

---

## 6. visualize.py — Plotly チャート

### cost_bar_chart(df) → go.Figure

- `go.Bar` トレース × 3（prevention / appraisal / failure）
- 積み上げ棒グラフ（`barmode="stack"`）
- 色:
  - prevention: `#16a34a`（緑）
  - appraisal: `#1e3a5f`（navy）
  - failure: `#dc2626`（赤）
- x軸: `month` 列、y軸: 金額（円）
- 高さ: 380px

### roi_line_chart(df, roi_series) → go.Figure

- ROI 折れ線（color `#d97706`、`mode="lines+markers"`）
- しきい値ライン（ROI=1.0、navy 点線、`line_dash="dash"`）
- x軸: month[1:] (ROI は2月目から)
- 高さ: 320px
- n == 1 のとき呼ばない

カラーテーマ（C-61〜C-70 統一）:
- Navy: `#1e3a5f`, Alert: `#dc2626`, Good: `#16a34a`, Warning: `#d97706`, BG: `#f5f7fa`

---

## 7. sample_data.py — デモ用サンプルデータ

```python
"""
12ヶ月（2024-01〜2024-12）

コスト設定:
- prevention: 500000 → 700000（段階的増加）
- appraisal:  300000 → 250000（効率化で微減）
- failure:   1500000 → 600000（改善効果で大幅減）

→ 後半月の ROI > 1.0 → verdict = "good" が期待される
"""
```

列構成: `month`, `prevention_cost`, `appraisal_cost`, `failure_cost`

---

## 8. app.py — UI レイアウト

```text
┌─────────────────┬──────────────────────────────────────────────┐
│ ⚙ 設定          │ KPI（4列）                                    │
│ [サンプルデータ] │  最新failure | 最新ROI | failure削減額 | verdict│
│ CSV upload      │                                              │
│ [▶ 分析実行]   │  コスト積み上げ棒グラフ  │  ROI推移折れ線       │
└─────────────────┴──────────────────────────────────────────────┘
```

### KPI 4列

| 列 | 表示内容 |
|----|---------|
| c1 | 最新月 failure_cost（`¥{v:,.0f}`）|
| c2 | 最新月 ROI（`{v:.2f}x`）または failure_ratio（1行時: `{v:.1%}`）|
| c3 | failure 削減額（初月 vs 最新月: `±¥{delta:,.0f}`、delta 引数）|
| c4 | verdict カード（good/warning/alert 色付き）|

### verdict ラベル

```python
_LABEL = {"good": "投資回収済み", "warning": "改善中", "alert": "要投資見直し"}
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
uid = write_upload("quality_cost_roi", filename, row_count)
# latest_roi が None（1行時）は failure_ratio を代用
value = result["latest_roi"] if result["latest_roi"] is not None else result["failure_ratio"]
write_kpi(uid, "quality_cost_roi", datetime.now().strftime("%Y-%m"), "roi", value, verdict)
```

### C-63 ダッシュボード — CARDS 追加

```python
{"system_id": "quality_cost_roi", "metric": "roi",
 "title": "品質コストROI", "fmt": lambda v: f"{v:.2f}x"}
```

---

## 10. テスト方針（test_analyze.py）

8テスト（TDD）:

| テスト名 | 内容 |
|---------|------|
| test_verdict_good | latest_roi > 1.0 → "good" |
| test_verdict_warning | 0 < latest_roi ≤ 1.0 → "warning" |
| test_verdict_alert | latest_roi ≤ 0 → "alert" |
| test_single_row_good | n=1, failure_ratio < 0.3 → "good" |
| test_single_row_alert | n=1, failure_ratio ≥ 0.5 → "alert" |
| test_roi_series_length | roi_series の長さが n-1 であること |
| test_output_keys | 全8キーが揃っていること |
| test_missing_column_raises | 必須列なし → ValueError |

---

## 11. catalog.yml エントリ

```yaml
- id: "C-71"
  name: "品質コストROI分析 — PAFモデル × 月次改善効果測定"
  industry: "製造"
  department: "品質"
  difficulty: "★★☆"
  status: "production-ready"
  priority: "B"
  path: "02_manufacturing/16_quality_cost_roi"
  demo: "streamlit run 02_manufacturing/16_quality_cost_roi/app.py"
  description: |
    月次の品質コスト（予防・評価・失敗）CSVをアップロードし、PAFモデルに基づくROIを自動計算。
    前月比 failure コスト削減額 / 投資額 > 1.0 → "good"（投資回収済み）という明快な verdict 設計。
    1行データ時は failure_ratio フォールバックで必ず verdict を返す堅牢な実装。
```

---

## 12. スコープ外（将来対応）

- 内部/外部失敗コストの分離（6列フォーマット）
- 業界ベンチマーク比較（同業他社の品質コスト比率）
- 予算計画モード（目標 ROI から逆算した必要投資額）
- 累積 ROI 表示（全期間通算）

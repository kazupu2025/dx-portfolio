# 工程間品質相関分析 設計仕様書

**作成日:** 2026-06-21
**システムID:** C-67
**難易度:** ★★☆
**カテゴリ:** 製造業 / 品質管理（QA）

---

## 1. 概要

複数工程の測定値（Wide 形式 CSV）をアップロードし、Pearson 相関行列を計算して
工程間の品質影響関係を自動可視化する。
最強相関ペアの |r| 値で verdict を判定し、結果を quality.db に書き込み
C-63 統合ダッシュボードに連携する。

---

## 2. 入力データ仕様

### CSV フォーマット（Wide 形式）

```csv
lot_id,process_A,process_B,process_C,process_D,process_E
L001,12.3,8.1,5.2,3.1,7.8
L002,11.8,7.9,5.0,3.3,8.1
L003,13.1,8.4,5.5,2.9,7.5
```

- `lot_id` 列（任意名）: ロット識別子（分析には使用しない）
- 工程列（複数）: 各工程の測定値（数値）
- 最低構成: 工程数 ≥ 2、サンプル数 n ≥ 3
- 推奨: n ≥ 20（相関係数の信頼性確保）

---

## 3. ファイル構成

```text
02_manufacturing/15_process_correlation/
├── app.py           # Streamlit UI + DB統合
├── analyze.py       # 相関計算ロジック（純粋関数）
├── visualize.py     # Plotly ヒートマップ + 散布図
├── sample_data.py   # デモCSV生成（5工程 × 50ロット）
├── STATUS.md
└── tests/
    ├── __init__.py
    └── test_analyze.py   # 8テスト（TDD）
```

---

## 4. データフロー

```text
CSV（lot_id + 工程列群）
  └─ app.py: 工程列チェックボックス選択 → 実行
       └─ analyze.py: run_analysis() → 相関行列 + verdict
            ├─ visualize.py: heatmap_chart() + scatter_chart()
            └─ _common/db_writer.py: write_kpi("process_correlation", ..., "max_r", max_abs_r, verdict)
                 └─ C-63 dashboard: process_correlation カード追加
```

---

## 5. analyze.py — 相関計算ロジック

### シグネチャ

```python
def run_analysis(
    df: pd.DataFrame,
    process_cols: list[str],
) -> dict:
```

### 処理フロー

1. `process_cols` の各列を `pd.to_numeric(errors="coerce")` で数値変換
2. NaN 行を `dropna()` で除去
3. バリデーション: `len(process_cols) < 2` または `n < 3` で ValueError
4. `df[process_cols].corr(method="pearson")` → 相関行列 `corr_df`
5. 全ペアの p値を `scipy.stats.pearsonr` で計算 → p値行列 `pvalue_df`
6. 対角要素を除いた |r| 最大ペア（`top_pair`）を特定
7. verdict 判定

### verdict 基準

| 条件 | verdict | 意味 |
|------|---------|------|
| max_abs_r ≥ 0.7 | `"good"` | 強い相関あり（工程間影響が明確）|
| max_abs_r ≥ 0.4 | `"warning"` | 中程度の相関（要監視）|
| max_abs_r < 0.4 | `"alert"` | 相関弱（工程間に関係なし）|

※ 相関の方向（正/負）は問わず絶対値で判定する。

### 出力 dict

```python
{
    "corr_df":      pd.DataFrame,   # 相関行列（process_cols × process_cols）
    "pvalue_df":    pd.DataFrame,   # p値行列（同形状）
    "top_pair":     tuple[str, str], # 最強相関ペア（列名）
    "top_r":        float,           # 最強ペアの相関係数（符号付き）
    "top_pvalue":   float,           # 最強ペアの p値
    "max_abs_r":    float,           # |r| 最大値（verdict 判定に使用）
    "n_samples":    int,             # 有効サンプル数
    "n_processes":  int,             # 工程数
    "verdict":      str,             # "good" | "warning" | "alert"
}
```

### エラー

```python
# バリデーション
if len(process_cols) < 2:
    raise ValueError("工程列は最低 2 列必要です。")
if n < 3:
    raise ValueError(f"有効サンプル数が不足しています（n={n}、最低 3 必要）。")
```

---

## 6. visualize.py — Plotly チャート

### heatmap_chart(corr_df, pvalue_df) → go.Figure

- `go.Heatmap` トレース
- カラースケール: -1（青 #1e3a5f）→ 0（白 #ffffff）→ +1（赤 #dc2626）
- `zmin=-1, zmax=1`
- セルテキスト: `f"{r:.2f}"` + p<0.05 のセルには `"*"` を追記
- 対角セルは 1.00（白）で表示
- 高さ: 400px

### scatter_chart(df, col_x, col_y, r, pvalue) → go.Figure

- 最強相関ペアの散布図（`go.Scatter(mode="markers")`）
- 回帰直線（`np.polyfit` + `go.Scatter(mode="lines")`、navy #1e3a5f）
- タイトル: `f"{col_x} vs {col_y}  r={r:.3f}  p={pvalue:.4f}"`
- 点: `#d97706`（warning amber）
- 高さ: 350px

カラーテーマ（C-61〜C-70 統一）:
- Navy: `#1e3a5f`, Alert: `#dc2626`, Good: `#16a34a`, Warning: `#d97706`, BG: `#f5f7fa`

---

## 7. sample_data.py — デモ用サンプルデータ

```python
"""
5工程（A〜E）× 50ロット

相関設定:
- A → B: r ≈ 0.85（強い正相関 → verdict = "good"）
- B → C: r ≈ 0.75（強い正相関）
- D: A と無相関
- E: ランダムノイズ

→ max_abs_r ≥ 0.7 → verdict = "good" が期待される
"""
rng = np.random.default_rng(42)
n = 50
```

列構成: `lot_id`, `process_A`, `process_B`, `process_C`, `process_D`, `process_E`

---

## 8. app.py — UI レイアウト

```text
┌─────────────────┬────────────────────────────────────────────┐
│ ⚙ 設定          │ KPI（4列）                                  │
│ [サンプルデータ] │  サンプル数 | 工程数 | 最強相関ペア(r) | verdict│
│ CSV upload      │                                            │
│ 工程列チェックBOX│──────────────────────────────────────────  │
│  ☑ process_A   │  ヒートマップ           │  最強ペア散布図      │
│  ☑ process_B   │  heatmap_chart()       │  scatter_chart()   │
│  ☑ process_C   │                        │                    │
│ [▶ 分析実行]   │  相関行列テーブル（p値付き）                   │
└─────────────────┴────────────────────────────────────────────┘
```

### KPI 4列

| 列 | 表示内容 |
|----|---------|
| c1 | 有効サンプル数（`{n_samples}件`）|
| c2 | 工程数（`{n_processes}工程`）|
| c3 | 最強相関ペア（`{col_x} × {col_y} r={top_r:.3f}`）|
| c4 | verdict カード（good/warning/alert 色付き）|

### verdict ラベル

```python
_LABEL = {"good": "強い相関あり", "warning": "中程度の相関", "alert": "相関なし"}
_COLOR = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
```

### 状態管理

- `st.session_state["df"]` でデータ保持
- `st.session_state["result"]` で分析結果保持
- `st.session_state["process_cols"]` で選択列保持

### エラーハンドリング

- 工程列 < 2 または n < 3 → `st.error()` + `st.stop()`
- DB 書き込み失敗 → `except Exception: st.caption(...)` でアプリ継続

---

## 9. DB 統合

```python
init_db()
uid = write_upload("process_correlation", filename, row_count)
write_kpi(uid, "process_correlation", datetime.now().strftime("%Y-%m"), "max_r", max_abs_r, verdict)
```

### C-63 ダッシュボード — CARDS 追加

```python
{"system_id": "process_correlation", "metric": "max_r",
 "title": "工程間最強相関（r）", "fmt": lambda v: f"{v:.3f}"}
```

---

## 10. テスト方針（test_analyze.py）

8テスト（TDD）:

| テスト名 | 内容 |
|---------|------|
| test_corr_matrix_shape | corr_df の shape が (n_proc, n_proc) であること |
| test_corr_diagonal_ones | 対角要素がすべて 1.0 であること |
| test_verdict_good | max_abs_r ≥ 0.7 → "good" |
| test_verdict_warning | 0.4 ≤ max_abs_r < 0.7 → "warning" |
| test_verdict_alert | max_abs_r < 0.4 → "alert" |
| test_top_pair_is_max | top_pair の |r| が全ペアの最大値と一致すること |
| test_output_keys | 全9出力キーが揃っていること |
| test_insufficient_data_raises | 工程 < 2 または n < 3 で ValueError |

---

## 11. catalog.yml エントリ

```yaml
- id: "C-67"
  name: "工程間品質相関分析 — Pearson 相関行列 × ヒートマップ"
  industry: "製造"
  department: "品質"
  difficulty: "★★☆"
  status: "production-ready"
  priority: "B"
  path: "02_manufacturing/15_process_correlation"
  demo: "streamlit run 02_manufacturing/15_process_correlation/app.py"
  description: |
    複数工程の測定値（Wide形式CSV）をアップロードし、Pearson相関行列を自動計算。
    工程間の品質影響関係をヒートマップで可視化し、最強相関ペアを散布図で詳細表示。
    max |r| ≥ 0.7 → "good"（強い相関）という verdict 設計で工程管理改善を支援。
```

---

## 12. スコープ外（将来対応）

- Spearman / Kendall 相関の選択
- 偏相関分析（交絡変数の除去）
- 時系列ラグ相関（工程間の遅延効果）
- 工程ネットワーク図（力学的レイアウト）

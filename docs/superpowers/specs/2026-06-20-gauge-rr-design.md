# ゲージR&R（MSA）設計仕様書

**作成日:** 2026-06-20
**難易度:** ★★☆
**カテゴリ:** 製造業 / 品質管理（QC）

---

## 1. 概要

測定データ（作業者 × 部品 × 繰り返し）を CSV でアップロードし、ANOVA 法による
ゲージR&R（Measurement System Analysis）を実行する。
繰り返し性（EV）・再現性（AV）・交互作用・部品変動を分離し、%GRR と ndc で
測定システムの合否を判定する。結果を quality.db に書き込み、C-63 ダッシュボードに連携する。

---

## 2. 入力データ仕様

### CSV フォーマット（ロング形式）

```csv
part,   operator, trial, value
P001,   田中,     1,     10.03
P001,   田中,     2,     10.05
P001,   田中,     3,     10.02
P001,   佐藤,     1,     10.01
...
```

- 1行 = 1測定値
- 最低構成: 2作業者 × 2部品 × 2繰り返し
- 推奨構成: 2〜3作業者 × 10部品 × 2〜3繰り返し（AIAG MSA 標準）
- 列名はアプリ内でマッピング（固定列名ではない）
- `trial` 列は UI での列選択に使用するが ANOVA 計算では使用しない（残差が自動的に EV を形成）

---

## 3. ファイル構成

```text
02_manufacturing/11_gauge_rr/
├── app.py           # Streamlit UI + DB統合
├── analyze.py       # ANOVA Gauge R&R 計算（テスト対象）
├── visualize.py     # Plotly 3チャート描画
├── sample_data.py   # デモ用CSV生成（90行）
├── STATUS.md
└── tests/
    ├── __init__.py
    └── test_analyze.py
```

---

## 4. データフロー

```text
CSVアップロード
  └─ app.py: 列選択（part / operator / trial / value）
       └─ analyze.py: ANOVA → 分散成分 → %GRR / ndc / verdict
            ├─ visualize.py: 3チャート描画
            └─ _common/db_writer.py: write_upload + write_kpi("grr_pct")
                 └─ C-63 dashboard.py: MSA カード表示
```

---

## 5. analyze.py — ANOVA Gauge R&R 計算

### ANOVA 2要因モデル（Part × Operator + 交互作用）

```text
測定値 = μ + Part_i + Operator_j + (Part×Operator)_ij + ε_ijk
```

### 分散分解手順

| ステップ | 計算 |
|---------|------|
| 1 | pandas groupby で MS_Error（繰り返し内分散）を計算 |
| 2 | scipy.stats.f_oneway または手動 SS 計算で SS_Part / SS_Operator / SS_Interaction を求める |
| 3 | MS = SS / df で各平均平方を計算 |
| 4 | 分散成分（σ²）を推定 |
| 5 | %GRR / ndc を計算 |

### 分散成分の推定式

```text
σ²_Equipment (EV²) = MS_Error
σ²_Interaction     = max(0, (MS_Interaction - MS_Error) / n_trials)
σ²_Appraiser (AV²) = max(0, (MS_Operator - MS_Interaction) / (n_parts × n_trials))
σ²_Part (PV²)      = max(0, (MS_Part - MS_Interaction) / (n_operators × n_trials))

GRR²  = EV² + AV²
TV²   = GRR² + PV²
```

※ 負の分散成分は 0 にクランプ（AIAG MSA 4th ed. 推奨）

### パーセント計算

```text
%GRR = 100 × GRR / TV
%EV  = 100 × EV  / TV
%AV  = 100 × AV  / TV
%Int = 100 × √σ²_Interaction / TV
%PV  = 100 × PV  / TV
```

### ndc（識別可能カテゴリ数）

```text
ndc = floor(1.41 × PV / GRR)
```

目標: ndc ≥ 5（5 以上で測定システムとして合格）

### 判定基準（AIAG MSA 第4版）

```text
%GRR < 10%  → "good"    (acceptable)
%GRR < 30%  → "warning" (may be acceptable depending on application)
%GRR ≥ 30%  → "alert"   (unacceptable — 要改善)
```

### run_analysis の出力形式

```python
{
    "ev":      float,   # σ_EV（繰り返し性）
    "av":      float,   # σ_AV（再現性）
    "int_":    float,   # σ_Interaction
    "pv":      float,   # σ_PV（部品変動）
    "grr":     float,   # σ_GRR
    "tv":      float,   # σ_TV（総変動）
    "grr_pct": float,   # %GRR
    "ev_pct":  float,   # %EV
    "av_pct":  float,   # %AV
    "int_pct": float,   # %Interaction
    "pv_pct":  float,   # %PV
    "ndc":     int,     # 識別可能カテゴリ数
    "verdict": str,     # "good" | "warning" | "alert"
    "anova_table": pd.DataFrame,  # SS / df / MS / F / p-value
}
```

---

## 6. visualize.py — Plotly チャート

### cov_chart(result) → go.Figure

- Components of Variation 棒グラフ（グループ棒グラフ）
- X軸: カテゴリ（%GRR, %EV, %AV, %Int, %PV）
- Y軸: パーセント値
- 基準線: 10%（good threshold）と 30%（alert threshold）を赤破線で表示
- 高さ: 280px

### scatter_chart(df, part_col, operator_col, value_col) → go.Figure

- 散布図: X軸=部品ID、Y軸=測定値
- 作業者ごとに異なる色でマーカーを描画
- 同一部品の測定値を細い線で結ぶ（ばらつきを視覚化）
- 高さ: 300px

### xbar_chart(df, part_col, operator_col, value_col) → go.Figure

- 作業者別の部品平均値を折れ線で描画
- 各作業者を異なる色・線種で表示
- 作業者間の「クセ（再現性）」を視覚化
- 高さ: 280px

カラーテーマ（C-61〜C-64 統一）:

- Navy: `#1e3a5f`, Alert: `#dc2626`, Good: `#16a34a`, BG: `#f5f7fa`
- フォント: BIZ UDGothic

---

## 7. sample_data.py — デモ用サンプルデータ

構成: **3作業者 × 10部品 × 3繰り返し = 90行**

意図的な違反埋め込み:

- 作業者「鈴木」: AV（再現性）を悪化させるため全部品に +0.15σ のバイアスを追加
- 部品 P005: EV（繰り返し性）を悪化させるため測定ノイズを 2倍に設定

---

## 8. app.py — UI レイアウト

```text
┌─────────────────┬──────────────────────────────────────────┐
│ ⚙ 設定          │ KPIサマリー（4列）                        │
│ CSVアップロード  │  %GRR  |  %EV  |  %AV  |  ndc           │
│ 部品列    [▾]  │                                          │
│ 作業者列  [▾]  │ Components of Variation 棒グラフ          │
│ 繰返列    [▾]  │                                          │
│ 測定値列  [▾]  │──────────────────────────────────────────│
│ [▶ 分析実行]   │ 散布図（部品 × 測定値 / 作業者別色分け）    │
│                 │──────────────────────────────────────────│
│                 │ Xbar 管理図（作業者別折れ線）              │
│                 │                                          │
│                 │ ANOVA テーブル（SS / df / MS / F / p値）  │
└─────────────────┴──────────────────────────────────────────┘
```

### 状態管理

- `st.session_state["df"]` でアップロードデータを保持
- `st.session_state["result"]` で分析結果を保持（ページリロード後も維持）

### エラーハンドリング

- サブグループ数が不足（作業者 < 2、部品 < 2、繰り返し < 2）→ `st.error()` + `st.stop()`
- DB書き込み失敗 → `except Exception: st.caption(...)` でアプリ継続

---

## 9. DB 統合

```python
init_db()
uid     = write_upload("msa", filename, row_count)
verdict = "good" if grr_pct < 10 else "warning" if grr_pct < 30 else "alert"
write_kpi(uid, "msa", datetime.now().strftime("%Y-%m"),
          "grr_pct", grr_pct, verdict)
```

### C-63 ダッシュボード — CARDS 追加

```python
{"system_id": "msa", "metric": "grr_pct",
 "title": "ゲージR&R（%GRR）", "fmt": lambda v: f"{v:.1f}%"}
```

verdict カラー: good（<10%）/ warning（<30%）/ alert（≥30%）

---

## 10. テスト方針（test_analyze.py）

| テスト名 | 内容 |
|---------|------|
| test_perfect_measurement | EV=0、AV=0 のとき %GRR≈0 |
| test_grr_pct_range | %GRR が 0〜100 の範囲内 |
| test_ndc_calculation | ndc = floor(1.41 × PV / GRR) の確認 |
| test_verdict_good | %GRR < 10 → "good" |
| test_verdict_warning | 10 ≤ %GRR < 30 → "warning" |
| test_verdict_alert | %GRR ≥ 30 → "alert" |
| test_negative_variance_clamped | 負の分散成分が 0 にクランプされること |
| test_insufficient_data_raises | 作業者 < 2 で ValueError |

最低 8 テスト（TDD: FAIL → 実装 → PASS）

---

## 11. スコープ外（将来対応）

- 規格幅（tolerance）ベースの %GRR 計算（現在は TV ベースのみ）
- Bias 分析・線形性分析（MSA の別手法）
- 繰り返し数が作業者・部品間で異なる不均衡データ

---

## 12. カラーテーマ（C-61〜C-64 統一）

| 用途 | カラーコード |
|------|------------|
| ヘッダー背景 | `#1e3a5f` |
| good | `#16a34a` / `#dcfce7` |
| warning | `#d97706` / `#fff7ed` |
| alert | `#dc2626` / `#fef2f2` |
| ページ背景 | `#f5f7fa` |
| フォント | BIZ UDGothic |

# 4M変更前後品質比較 設計仕様書

**作成日:** 2026-06-20
**難易度:** ★★☆
**カテゴリ:** 製造業 / 品質管理（QC）

---

## 1. 概要

4M変更（材料・機械・方法・人）の前後測定データを CSV でアップロードし、
t検定 + Mann-Whitney U検定の両方を実行して統計的有意差を自動判定する。
正規性検定（Shapiro-Wilk）の結果に基づき推奨検定を自動選択し、
製造現場の変化点管理を支援する。結果を quality.db に書き込み、C-63 ダッシュボードに連携する。

---

## 2. 入力データ仕様

### CSV フォーマット（Wide形式 / group列 + value列）

```csv
group,measurement
before,10.2
before,10.5
before,10.3
after,10.8
after,11.1
after,10.9
```

- `group` 列: 前後を識別する文字列（例: "before"/"after"、"変更前"/"変更後"）
- `value` 列: 測定値（数値）
- 最低構成: 各グループ n ≥ 3
- 推奨: 各グループ n ≥ 20（中心極限定理が働く）

---

## 3. ファイル構成

```text
02_manufacturing/12_4m_change/
├── app.py           # Streamlit UI + DB統合
├── analyze.py       # 検定ロジック（テスト対象）
├── visualize.py     # Plotly 2チャート
├── sample_data.py   # デモCSV生成（before 30行 + after 30行）
├── STATUS.md
└── tests/
    ├── __init__.py
    └── test_analyze.py   # 8テスト（TDD）
```

---

## 4. データフロー

```text
CSVアップロード（group列 + value列）
  └─ app.py: 列選択・before/afterラベル指定
       └─ analyze.py: run_analysis() → 検定結果 dict
            ├─ visualize.py: hist_chart() + box_chart()
            └─ _common/db_writer.py: write_kpi("4m_change", ..., "p_value", p, verdict)
                 └─ C-63 dashboard: 4m_change カード追加
```

---

## 5. analyze.py — 検定ロジック

### シグネチャ

```python
def run_analysis(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    before_label: str,
    after_label: str,
) -> dict:
```

### 処理フロー

1. `before_label` / `after_label` でグループ分離
2. n < 3 のグループがあれば ValueError
3. **Shapiro-Wilk 正規性検定**（各グループ、n ≤ 5000）
   - `scipy.stats.shapiro`
   - p ≥ 0.05 → 正規分布と見なす
4. **t検定**（独立2標本、equal_var=False / Welch）
   - `scipy.stats.ttest_ind(a, b, equal_var=False)`
   - 効果量: Cohen's d = (mean_after - mean_before) / pooled_std
   - pooled_std = sqrt(((n_b-1)×std_b² + (n_a-1)×std_a²) / (n_b + n_a - 2))
5. **Mann-Whitney U検定**（ノンパラメトリック）
   - `scipy.stats.mannwhitneyu(a, b, alternative='two-sided')`
   - 効果量: rank-biserial r = 1 - (2×U) / (n_before × n_after)
6. **推奨検定の選択**
   - 両グループとも正規（shapiro p ≥ 0.05）→ `recommended = "t"`
   - それ以外 → `recommended = "mw"`
7. **verdict 判定**（推奨検定の p 値と効果量を使用）

### verdict 基準

| 条件 | verdict | 意味 |
|------|---------|------|
| 推奨 p ≥ 0.05 | `"good"` | 変化なし（工程安定） |
| p < 0.05 かつ 効果量 < 0.5 | `"warning"` | 有意差あり・小さな変化 |
| p < 0.05 かつ 効果量 ≥ 0.5 | `"alert"` | 有意差あり・大きな変化 |

### 出力 dict

```python
{
    # 記述統計
    "n_before": int,
    "n_after": int,
    "mean_before": float,
    "mean_after": float,
    "std_before": float,
    "std_after": float,
    # 正規性検定
    "shapiro_before_p": float,
    "shapiro_after_p": float,
    "normal_before": bool,
    "normal_after": bool,
    # t検定
    "t_stat": float,
    "t_pvalue": float,
    "cohens_d": float,
    # Mann-Whitney U検定
    "mw_stat": float,
    "mw_pvalue": float,
    "rank_biserial_r": float,
    # 推奨・総合
    "recommended": str,    # "t" または "mw"
    "p_value": float,      # 推奨検定のp値
    "effect_size": float,  # 推奨検定の効果量（絶対値）
    "verdict": str,        # "good" | "warning" | "alert"
}
```

---

## 6. visualize.py — Plotly チャート

### hist_chart(before, after, before_label, after_label) → go.Figure

- 半透明ヒストグラム重ね表示（opacity=0.6）
- before = navy (#1e3a5f)、after = alert red (#dc2626)
- 高さ: 300px

### box_chart(before, after, before_label, after_label) → go.Figure

- 箱ひげ図2本（前後並列）
- 中央値・IQR・外れ値（points="outliers"）を表示
- before = navy、after = alert red
- 高さ: 300px

カラーテーマ（C-61〜C-65 統一）:
- Navy: `#1e3a5f`, Alert: `#dc2626`, Good: `#16a34a`, Warning: `#d97706`, BG: `#f5f7fa`
- フォント: BIZ UDGothic

---

## 7. sample_data.py — デモ用サンプルデータ

```python
"""
before: 平均 10.0、std=0.30、30行（正常工程）
after:  平均 10.6、std=0.50、30行（4M変更後に悪化）
→ p < 0.05、効果量大 → verdict = "alert" が期待される
"""
rng = np.random.default_rng(42)
```

列構成: `group`, `measurement`

---

## 8. app.py — UI レイアウト

```text
┌─────────────────┬────────────────────────────────────────────┐
│ ⚙ 設定          │ KPI（4列）                                  │
│ [サンプルデータ] │  p値  |  効果量  |  推奨検定  |  verdict    │
│ CSV upload      │                                            │
│ group列   [▾]  │──────────────────────────────────────────  │
│ value列   [▾]  │  ヒストグラム重ね   │  Box plot 前後比較     │
│ beforeラベル[▾] │  (hist_chart)      │  (box_chart)          │
│ afterラベル [▾] │                                            │
│ [▶ 分析実行]   │──────────────────────────────────────────  │
│                 │  検定結果テーブル                           │
│                 │  （t検定 / Mann-Whitney / 推奨ハイライト）  │
└─────────────────┴────────────────────────────────────────────┘
```

### 検定結果テーブル構成

| 検定 | 統計量 | p値 | 効果量 | 推奨 |
|------|--------|-----|--------|------|
| t検定（Welch）| t_stat | t_pvalue | Cohen's d | ★ or — |
| Mann-Whitney U | mw_stat | mw_pvalue | rank-biserial r | ★ or — |

### 状態管理

- `st.session_state["df"]` でデータ保持
- `st.session_state["result"]` で分析結果保持（ページリロード後も維持）

### エラーハンドリング

- n < 3 → `st.error()` + `st.stop()`
- DB書き込み失敗 → `except Exception: st.caption(...)` でアプリ継続

---

## 9. DB 統合

```python
init_db()
uid = write_upload("4m_change", filename, row_count)
write_kpi(uid, "4m_change", datetime.now().strftime("%Y-%m"), "p_value", p_value, verdict)
```

### C-63 ダッシュボード — CARDS 追加

```python
{"system_id": "4m_change", "metric": "p_value",
 "title": "4M変更有意差（p値）", "fmt": lambda v: f"{v:.4f}"}
```

verdict カラー: good（p≥0.05）/ warning（p<0.05 小効果）/ alert（p<0.05 大効果）

---

## 10. テスト方針（test_analyze.py）

| テスト名 | 内容 |
|---------|------|
| test_no_significant_diff | 同一分布 → p ≥ 0.05 → "good" |
| test_significant_large_effect | 平均差大 → p < 0.05 かつ効果量 ≥ 0.5 → "alert" |
| test_significant_small_effect | 平均差小・n大 → p < 0.05 かつ効果量 < 0.5 → "warning" |
| test_normality_selects_ttest | 両グループ正規 → recommended="t" |
| test_nonnormal_selects_mannwhitney | 非正規分布 → recommended="mw" |
| test_cohens_d_formula | Cohen's d = (mean_after - mean_before) / pooled_std |
| test_output_keys | 全出力キーが揃っていること |
| test_insufficient_data_raises | n < 3 で ValueError |

最低 8 テスト（TDD: FAIL → 実装 → PASS）

---

## 11. catalog.yml エントリ

```yaml
- id: "C-66"
  name: "4M変更前後品質比較 — 変化点有意差検定（t検定/Mann-Whitney）"
  industry: "製造"
  department: "生産・品質"
  difficulty: "★★☆"
  status: "production-ready"
  priority: "B"
  path: "02_manufacturing/12_4m_change"
  demo: "streamlit run 02_manufacturing/12_4m_change/app.py"
  description: |
    4M変更（材料・機械・方法・人）前後の測定データを比較し、統計的有意差を自動判定。
    t検定（Welch）とMann-Whitney U検定を両方実行し、Shapiro-Wilk正規性検定で推奨手法を自動選択。
    効果量（Cohen's d / rank-biserial r）で変化の大きさも定量化する。
```

---

## 12. スコープ外（将来対応）

- 多グループ比較（3グループ以上の ANOVA）
- 対応のある t検定（同一個体の前後測定）
- 信頼区間の可視化
- 検出力（Power）計算

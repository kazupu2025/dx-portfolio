# 不良モード別パレート × 時系列複合分析 設計仕様書

**作成日:** 2026-06-20
**システムID:** C-69
**難易度:** ★★☆
**カテゴリ:** 製造業 / 品質管理（QC・QA）

---

## 1. 概要

月次集計済みの不良モード別件数データを CSV でアップロードし、
パレート分析（降順集計 + 累積80%判定）と月別時系列推移グラフを自動生成する。
"vital few"（80%以内の支配的不良モード）を自動特定し、直近月の悪化傾向を verdict で通知する。
結果を quality.db に書き込み、C-63 統合ダッシュボードに連携する。

---

## 2. 入力データ仕様

### CSV フォーマット（月次集計済み形式）

```csv
year_month,defect_mode,count
2024-01,バリ,45
2024-01,寸法不良,22
2024-01,表面傷,12
2024-02,バリ,38
2024-02,寸法不良,25
```

- `year_month` 列: 年月文字列（例: "2024-01"）
- `defect_mode` 列: 不良モード名（文字列）
- `count` 列: 月次件数（整数）
- 最低構成: 2ヶ月分 × 2モード以上
- パレート集計は全期間合計で実施

---

## 3. ファイル構成

```text
02_manufacturing/13_defect_pareto/
├── app.py           # Streamlit UI + DB統合
├── analyze.py       # 集計・パレート計算（テスト対象）
├── visualize.py     # Plotly 2チャート
├── sample_data.py   # デモCSV生成（5モード × 12ヶ月）
├── STATUS.md
└── tests/
    ├── __init__.py
    └── test_analyze.py   # 8テスト（TDD）
```

---

## 4. データフロー

```text
CSV（year_month, defect_mode, count）
  └─ app.py: 列選択
       └─ analyze.py: run_analysis() → pareto_df + trend_df + verdict
            ├─ visualize.py: pareto_chart() + trend_chart()
            └─ _common/db_writer.py: write_kpi("defect_pareto", ..., "top_mode_pct", pct, verdict)
                 └─ C-63 dashboard: defect_pareto カード追加
```

---

## 5. analyze.py — 集計・パレートロジック

### シグネチャ

```python
def run_analysis(
    df: pd.DataFrame,
    date_col: str,
    mode_col: str,
    count_col: str,
) -> dict:
```

### 処理フロー

1. `count_col` を数値型に強制変換（`pd.to_numeric(errors="coerce")`）、NaN 行を除去
2. 最低検証: モード数 < 2 または月数 < 2 で ValueError
3. **パレート集計（全期間）:**
   - モード別合計件数を計算（降順ソート）
   - 累積割合 `cumulative_pct = cumsum / total * 100`
   - `pareto_df`: columns = [mode_col, "count", "cumulative_pct"]
4. **vital few 特定:**
   - `cumulative_pct <= 80` の行群（ただし最初の1行は必ず含む）
   - `vital_few`: モード名リスト
5. **月別推移ピボット（trend_df）:**
   - `pivot_table(index=date_col, columns=mode_col, values=count_col, aggfunc="sum", fill_value=0)`
   - 列順: パレート降順（top_mode が先頭）
6. **verdict 判定（直近月 vs 前月 合計件数比較）:**
   - 月ソート後の最後2ヶ月を使用
   - 月ごとに全モード合計を計算

### verdict 基準

| 条件 | verdict | 意味 |
|------|---------|------|
| latest_total < prev_total × 0.9 | `"good"` | 10%以上改善 |
| latest_total ≤ prev_total × 1.1 | `"warning"` | 横ばい（±10%以内）|
| latest_total > prev_total × 1.1 | `"alert"` | 10%以上悪化 |

月が1ヶ月分しかない場合: `prev_total = latest_total` → `"warning"`

### 出力 dict

```python
{
    "pareto_df":     pd.DataFrame,  # columns: [mode_col, "count", "cumulative_pct"] 降順
    "trend_df":      pd.DataFrame,  # pivot: index=year_month, columns=mode (パレート降順)
    "top_mode":      str,           # 最多不良モード名
    "top_mode_pct":  float,         # 最多モードの構成比（%）
    "total_count":   int,           # 全期間合計件数
    "vital_few":     list[str],     # 累積80%以内のモード群（最低1件）
    "latest_month":  str,           # 直近年月
    "latest_total":  int,           # 直近月の全モード合計
    "prev_total":    int,           # 前月の全モード合計
    "verdict":       str,           # "good" | "warning" | "alert"
}
```

---

## 6. visualize.py — Plotly チャート

### pareto_chart(pareto_df, mode_col) → go.Figure

- 主軸（左）: 棒グラフ（件数、navy #1e3a5f）
- 副軸（右）: 累積% 折れ線（orange #d97706）+ マーカー
- 80% 閾値破線（alert red #dc2626、dash="dash"）
- vital few の棒を alert red に色変更（その他は navy）
- 高さ: 350px

### trend_chart(trend_df) → go.Figure

- モード別月次推移 折れ線グラフ
- 最大5モード表示（パレート降順 — top_mode が先頭）
- カラーパレット: `["#1e3a5f", "#dc2626", "#16a34a", "#d97706", "#7c3aed"]`
- 高さ: 300px

カラーテーマ（C-61〜C-66 統一）:
- Navy: `#1e3a5f`, Alert: `#dc2626`, Good: `#16a34a`, Warning: `#d97706`, BG: `#f5f7fa`
- フォント: BIZ UDGothic

---

## 7. sample_data.py — デモ用サンプルデータ

```python
"""
5不良モード × 12ヶ月（2024-01〜2024-12）= 60行

設定:
- バリ: 全体の約50%（dominant mode → vital few に確実に入る）
- 寸法不良: 約25%
- 表面傷: 約15%
- 欠け: 約7%
- 異物混入: 約3%

直近月（2024-12）: 前月比 +25% → verdict = "alert" が期待される
"""
rng = np.random.default_rng(42)
```

列構成: `year_month`, `defect_mode`, `count`

---

## 8. app.py — UI レイアウト

```text
┌─────────────────┬────────────────────────────────────────────┐
│ ⚙ 設定          │ KPI（4列）                                  │
│ [サンプルデータ] │  合計件数  |  最多モード  |  vital few数  | verdict│
│ CSV upload      │                                            │
│ date列    [▾]  │──────────────────────────────────────────  │
│ mode列    [▾]  │  パレート図             │  月別推移グラフ      │
│ count列   [▾]  │  pareto_chart()        │  trend_chart()     │
│ [▶ 分析実行]   │                                            │
└─────────────────┴────────────────────────────────────────────┘
```

### KPI 4列

| 列 | 表示内容 |
|----|---------|
| c1 | 全期間合計件数（`{total_count:,}件`）|
| c2 | 最多不良モード（`top_mode`）+ 構成比 |
| c3 | vital few 数（`{len(vital_few)}モード で80%`）|
| c4 | verdict カード（good/warning/alert 色付き）|

### 状態管理

- `st.session_state["df"]` でデータ保持
- `st.session_state["result"]` で分析結果保持

### エラーハンドリング

- モード数 < 2 または月数 < 2 → `st.error()` + `st.stop()`
- DB書き込み失敗 → `except Exception: st.caption(...)` でアプリ継続

---

## 9. DB 統合

```python
init_db()
uid = write_upload("defect_pareto", filename, row_count)
write_kpi(uid, "defect_pareto", latest_month, "top_mode_pct", top_mode_pct, verdict)
```

### C-63 ダッシュボード — CARDS 追加

```python
{"system_id": "defect_pareto", "metric": "top_mode_pct",
 "title": "最多不良モード構成比", "fmt": lambda v: f"{v:.1f}%"}
```

---

## 10. テスト方針（test_analyze.py）

| テスト名 | 内容 |
|---------|------|
| test_pareto_sorted_descending | pareto_df の count 列が降順であること |
| test_cumulative_pct_reaches_100 | 最終行の cumulative_pct ≈ 100.0 |
| test_vital_few_contains_top_mode | vital_few の先頭が top_mode と一致すること |
| test_vital_few_threshold | vital_few 累積が 80% 以上であること |
| test_verdict_good | 直近月 < 前月×0.9 → "good" |
| test_verdict_warning | 直近月 ≈ 前月 → "warning" |
| test_verdict_alert | 直近月 > 前月×1.1 → "alert" |
| test_output_keys | 全出力キーが揃っていること |

最低 8 テスト（TDD: FAIL → 実装 → PASS）

---

## 11. catalog.yml エントリ

```yaml
- id: "C-69"
  name: "不良モード別パレート × 時系列複合分析"
  industry: "製造"
  department: "生産・品質"
  difficulty: "★★☆"
  status: "production-ready"
  priority: "B"
  path: "02_manufacturing/13_defect_pareto"
  demo: "streamlit run 02_manufacturing/13_defect_pareto/app.py"
  description: |
    月次集計済みの不良モード別件数データをパレート分析と時系列推移グラフで可視化。
    累積80%以内の"vital few"（支配的不良モード群）を自動特定し、
    直近月の悪化傾向を verdict（good/warning/alert）で通知する。
```

---

## 12. スコープ外（将来対応）

- 不良モードのドリルダウン（工程・ロット別詳細）
- 季節性補正・移動平均
- 目標値ラインの設定と達成率表示
- PDF レポート出力

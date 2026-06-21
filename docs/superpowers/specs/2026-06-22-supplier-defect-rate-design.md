# 協力会社別受入不良率月報 設計仕様書

**作成日:** 2026-06-22
**システムID:** C-73
**難易度:** ★★★
**カテゴリ:** 製造業 / 品質保証（QA）

---

## 1. 概要

協力会社（仕入先）ごとの月次受入検査結果（受入数・不良数）を CSV でアップロードし、
不良率を自動計算して協力会社別・月次トレンドを可視化する。
平均不良率 ≤ 1.0% → "good" という明快な verdict 設計で、
結果を quality.db に書き込んで C-63 統合ダッシュボードに連携する。

---

## 2. 入力データ仕様

### CSV フォーマット（Wide 4列・1行=1協力会社×1ヶ月）

```csv
supplier,month,incoming_qty,defect_qty
A社,2024-01,500,8
B社,2024-01,300,15
C社,2024-01,800,4
A社,2024-02,520,6
```

- `supplier`: 協力会社名（文字列）
- `month`: 年月（YYYY-MM 形式）
- `incoming_qty`: 受入数（正の整数）
- `defect_qty`: 不良数（0以上の整数）
- 最低構成: n ≥ 1

---

## 3. ファイル構成

```text
02_manufacturing/19_supplier_defect_rate/
├── app.py           # Streamlit UI + DB 統合
├── analyze.py       # 不良率計算ロジック（純粋関数）
├── visualize.py     # Plotly 月次トレンド + 協力会社別横棒
├── sample_data.py   # デモ CSV 生成（5協力会社 × 6ヶ月）
├── STATUS.md
└── tests/
    ├── __init__.py
    └── test_analyze.py   # 8テスト（TDD）
```

---

## 4. データフロー

```text
CSV（supplier, month, incoming_qty, defect_qty）
  └─ app.py
       └─ analyze.py: run_analysis() → 不良率 + verdict
            ├─ visualize.py: defect_rate_chart() + supplier_bar_chart()
            └─ _common/db_writer.py: write_kpi("supplier_defect_rate", ..., "defect_rate", avg, verdict)
                  └─ C-63 dashboard: supplier_defect_rate カード追加
```

---

## 5. analyze.py — 計算ロジック

### 必須列

```python
REQUIRED_COLS = ["supplier", "month", "incoming_qty", "defect_qty"]
```

### 処理フロー

1. 必須列の存在確認 → なければ ValueError
2. `incoming_qty`, `defect_qty` を `pd.to_numeric(errors="coerce")` で変換 + NaN 行 `dropna()`
3. `incoming_qty <= 0` の行を除外
4. n < 1 で ValueError（"有効なデータがありません"）
5. `defect_rate = defect_qty / incoming_qty * 100`（行ごと）
6. `avg_defect_rate = total_defect_qty / total_incoming_qty * 100`（加重平均）
7. verdict 判定

### verdict 基準

| 条件 | verdict | 意味 |
|------|---------|------|
| avg_defect_rate ≤ 1.0 | `"good"` | 品質良好 |
| avg_defect_rate ≤ 3.0 | `"warning"` | 要注意 |
| avg_defect_rate > 3.0 | `"alert"` | 要改善 |

### シグネチャ

```python
def run_analysis(df: pd.DataFrame) -> dict:
```

### 出力 dict（6キー）

```python
{
    "result_df":       pd.DataFrame,  # supplier + month + incoming_qty + defect_qty + defect_rate 列
    "avg_defect_rate": float,         # 加重平均不良率（%）
    "worst_supplier":  str,           # 最高不良率の協力会社
    "best_supplier":   str,           # 最低不良率の協力会社
    "n_suppliers":     int,           # ユニーク協力会社数
    "verdict":         str,           # "good" | "warning" | "alert"
}
```

### worst/best_supplier の計算

```python
# 協力会社ごとの加重平均不良率で比較
supplier_rates = (
    df.groupby("supplier")
    .apply(lambda g: g["defect_qty"].sum() / g["incoming_qty"].sum() * 100)
)
worst_supplier = str(supplier_rates.idxmax())
best_supplier  = str(supplier_rates.idxmin())
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

### defect_rate_chart(result_df) → go.Figure

- 協力会社 × 月ごとの不良率をグループ棒グラフ（`barmode="group"`）
- x 軸: month / トレース: supplier（各社に異なる色）
- しきい値横線:
  - `add_hline(y=3.0, line_dash="dash", line_color="#dc2626")` — alert ライン
  - `add_hline(y=1.0, line_dash="dash", line_color="#16a34a")` — good ライン
- タイトル: "協力会社別 月次不良率推移"
- 高さ: 380px、BG: `#f5f7fa`

### supplier_bar_chart(result_df) → go.Figure

- 協力会社別の加重平均不良率を横棒グラフ（`orientation="h"`）
- 棒の色: avg ≤ 1.0 → `#16a34a` / ≤ 3.0 → `#d97706` / > 3.0 → `#dc2626`
- しきい値縦線: `add_vline(x=1.0, #16a34a, dash)` + `add_vline(x=3.0, #dc2626, dash)`
- タイトル: "協力会社別 平均不良率"
- 高さ: 320px、BG: `#f5f7fa`

カラーテーマ（統一）:
- Navy: `#1e3a5f`, Alert: `#dc2626`, Good: `#16a34a`, Warning: `#d97706`, BG: `#f5f7fa`

---

## 7. sample_data.py — デモ用サンプルデータ

```python
"""
5協力会社（A社〜E社）× 6ヶ月（2024-01〜2024-06）= 30行

設定:
- A社: 不良率 ≈ 0.8%（優良）
- B社: 不良率 ≈ 4.5%（要改善）
- C社: 不良率 ≈ 1.5%（要注意）
- D社: 不良率 ≈ 0.5%（優良）
- E社: 不良率 ≈ 2.8%（要注意）
→ avg ≈ 2.0% → verdict = "warning"
"""
```

列構成: `supplier`, `month`, `incoming_qty`, `defect_qty`

---

## 8. app.py — UI レイアウト

```text
┌─────────────────┬──────────────────────────────────────────────┐
│ ⚙ 設定          │ KPI（4列）                                    │
│ [サンプルデータ] │  協力会社数 | 平均不良率 | 最良協力会社 | verdict│
│ CSV upload      │                                              │
│ [▶ 分析実行]   │  月次トレンドグラフ | 協力会社別平均横棒グラフ   │
└─────────────────┴──────────────────────────────────────────────┘
```

### KPI 4列

| 列 | 表示内容 |
|----|---------|
| c1 | 協力会社数（`{n_suppliers}社`）|
| c2 | 平均不良率（`{avg_defect_rate:.2f}%`）|
| c3 | 最良協力会社（`{best_supplier}`）|
| c4 | verdict カード（good/warning/alert 色付き）|

### verdict ラベル

```python
_LABEL = {"good": "品質良好", "warning": "要注意", "alert": "要改善"}
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
uid = write_upload("supplier_defect_rate", filename, row_count)
write_kpi(
    uid, "supplier_defect_rate",
    datetime.now().strftime("%Y-%m"),
    "defect_rate", avg_defect_rate, verdict,
)
```

### C-63 ダッシュボード — CARDS 追加

```python
{"system_id": "supplier_defect_rate", "metric": "defect_rate",
 "title": "受入不良率（平均）", "fmt": lambda v: f"{v:.2f}%"}
```

---

## 10. テスト方針（test_analyze.py）

8テスト（TDD）:

| テスト名 | 内容 |
|---------|------|
| `test_verdict_good` | avg ≤ 1.0 → "good" |
| `test_verdict_warning` | 1.0 < avg ≤ 3.0 → "warning" |
| `test_verdict_alert` | avg > 3.0 → "alert" |
| `test_defect_rate_calculation` | defect_qty/incoming_qty*100 の正確性 |
| `test_weighted_average` | 複数行の加重平均が単純平均と異なることの確認 |
| `test_worst_supplier` | 不良率最高の協力会社が worst_supplier に入ること |
| `test_output_keys` | 全6キーが揃っていること |
| `test_missing_column_raises` | 必須列なし → ValueError |

---

## 11. catalog.yml エントリ

```yaml
- id: "C-73"
  name: "協力会社別受入不良率月報"
  industry: "製造"
  department: "品質保証"
  difficulty: "★★★"
  status: "production-ready"
  priority: "B"
  path: "02_manufacturing/19_supplier_defect_rate"
  demo: "streamlit run 02_manufacturing/19_supplier_defect_rate/app.py"
  description: |
    協力会社（仕入先）ごとの月次受入検査データ（受入数・不良数）を CSV でアップロードし、
    不良率を自動計算。平均不良率 ≤ 1.0% → "good" の明快な verdict 設計。
    月次トレンドグラフと協力会社別平均横棒グラフで改善ポイントを可視化。
```

---

## 12. スコープ外（将来対応）

- 不良カテゴリ別の内訳（寸法不良・外観不良・機能不良）
- 前月比トレンドの自動アラート
- 協力会社評価スコアとの連携（C-68 との統合）

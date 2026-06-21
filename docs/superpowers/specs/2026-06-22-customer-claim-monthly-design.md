# 顧客クレーム件数・原因分類 月次集計 設計仕様書

**作成日:** 2026-06-22
**システムID:** C-74
**難易度:** ★★★
**カテゴリ:** 製造業 / 品質保証（QA）

---

## 1. 概要

顧客別・原因分類別のクレーム件数を CSV でアップロードし、月次推移と原因分類内訳を自動集計する。
平均月次クレーム数 ≤ 5件 → "good" の明快な verdict 設計で、結果を quality.db に書き込んで C-63 統合ダッシュボードに連携する。

---

## 2. 入力データ仕様

### CSV フォーマット（Long 4列・1行=1顧客×1月×1原因分類）

```csv
customer,month,category,count
A社,2024-01,寸法不良,2
A社,2024-01,外観不良,1
B社,2024-01,寸法不良,5
A社,2024-02,寸法不良,3
```

- `customer`: 顧客名（文字列）
- `month`: 年月（YYYY-MM 形式）
- `category`: 原因分類（文字列）
- `count`: クレーム件数（0以上の整数）
- 最低構成: n ≥ 1

---

## 3. ファイル構成

```text
02_manufacturing/20_customer_claim_monthly/
├── app.py           # Streamlit UI + DB 統合
├── analyze.py       # クレーム集計ロジック（純粋関数）
├── visualize.py     # Plotly 月次トレンド + 原因分類横棒
├── sample_data.py   # デモ CSV 生成（5顧客 × 6ヶ月 × 3分類）
├── STATUS.md
└── tests/
    ├── __init__.py
    └── test_analyze.py   # 8テスト（TDD）
```

---

## 4. データフロー

```text
CSV（customer, month, category, count）
  └─ app.py
       └─ analyze.py: run_analysis() → クレーム集計 + verdict
            ├─ visualize.py: claim_trend_chart() + category_chart()
            └─ _common/db_writer.py: write_kpi("customer_claim_monthly", ..., "claim_count", total, verdict)
                  └─ C-63 dashboard: customer_claim_monthly カード追加
```

---

## 5. analyze.py — 計算ロジック

### 必須列

```python
REQUIRED_COLS = ["customer", "month", "category", "count"]
```

### 処理フロー

1. 必須列の存在確認 → なければ ValueError
2. `count` を `pd.to_numeric(errors="coerce")` で変換 + NaN 行 `dropna()`
3. `count < 0` の行を除外（0件は有効）
4. n < 1 で ValueError（"有効なデータがありません"）
5. `total_claims = int(df["count"].sum())`
6. `n_months = df["month"].nunique()`
7. `avg_monthly_claims = total_claims / n_months`
8. `top_category`: category ごとの count 合計が最大のもの
9. `worst_customer`: customer ごとの count 合計が最大のもの
10. verdict 判定

### verdict 基準

| 条件 | verdict | 意味 |
|------|---------|------|
| avg_monthly_claims ≤ 5.0 | `"good"` | クレーム少 |
| avg_monthly_claims ≤ 15.0 | `"warning"` | 要注意 |
| avg_monthly_claims > 15.0 | `"alert"` | 要改善 |

### シグネチャ

```python
def run_analysis(df: pd.DataFrame) -> dict:
```

### 出力 dict（7キー）

```python
{
    "result_df":          pd.DataFrame,  # 元データ（count 数値型確保済み）
    "total_claims":       int,           # 全期間クレーム総件数
    "avg_monthly_claims": float,         # 月次平均クレーム数
    "top_category":       str,           # 最多原因分類
    "worst_customer":     str,           # 最多クレーム顧客
    "n_customers":        int,           # ユニーク顧客数
    "verdict":            str,           # "good" | "warning" | "alert"
}
```

### top_category / worst_customer の計算

```python
category_totals = data.groupby("category")["count"].sum()
top_category = str(category_totals.idxmax())

customer_totals = data.groupby("customer")["count"].sum()
worst_customer = str(customer_totals.idxmax())
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

### claim_trend_chart(result_df) → go.Figure

- 顧客 × 月ごとのクレーム件数をグループ棒グラフ（`barmode="group"`）
- x 軸: month / トレース: customer（各社に異なる色）
- pivot で月 × 顧客のマトリクスを作成してから描画
- しきい値横線:
  - `add_hline(y=15.0, line_dash="dash", line_color="#dc2626")` — alert ライン
  - `add_hline(y=5.0, line_dash="dash", line_color="#16a34a")` — good ライン
- タイトル: "顧客別 月次クレーム件数推移"
- 高さ: 380px、BG: `#f5f7fa`

### category_chart(result_df) → go.Figure

- 原因分類別の総クレーム件数を横棒グラフ（`orientation="h"`）
- 件数降順ソート（多い順が上に表示）
- 棒の色: `#1e3a5f`（navy 統一）
- テキスト: 件数を棒の外側に表示
- タイトル: "原因分類別 クレーム件数"
- 高さ: 320px、BG: `#f5f7fa`

カラーテーマ（統一）:
- Navy: `#1e3a5f`, Alert: `#dc2626`, Good: `#16a34a`, Warning: `#d97706`, BG: `#f5f7fa`

---

## 7. sample_data.py — デモ用サンプルデータ

```
5顧客（A社〜E社）× 6ヶ月（2024-01〜2024-06）× 3原因分類
= 90行

設定:
- 寸法不良: 最多（top_category）
- A社: 少ない（good水準）
- B社: 中程度
- C社: 最多（worst_customer）
- D社: 少ない
- E社: 中程度
→ avg_monthly ≈ 12件 → verdict = "warning"
```

列構成: `customer`, `month`, `category`, `count`

---

## 8. app.py — UI レイアウト

```text
┌─────────────────┬──────────────────────────────────────────────┐
│ ⚙ 設定          │ KPI（4列）                                    │
│ CSV upload      │  顧客数 | 月次平均 | 最多原因分類 | verdict    │
│ [サンプルデータ] │                                              │
│ [▶ 分析実行]   │  月次トレンドグラフ | 原因分類横棒グラフ        │
└─────────────────┴──────────────────────────────────────────────┘
```

### KPI 4列

| 列 | 表示内容 |
|----|---------|
| c1 | 顧客数（`{n_customers}社`）|
| c2 | 月次平均クレーム数（`{avg:.1f}件`）|
| c3 | 最多原因分類（`{top_category}`）|
| c4 | verdict カード（good/warning/alert 色付き）|

### verdict ラベル

```python
_LABEL = {"good": "クレーム少", "warning": "要注意", "alert": "要改善"}
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
uid = write_upload("customer_claim_monthly", filename, row_count)
write_kpi(
    uid, "customer_claim_monthly",
    datetime.now().strftime("%Y-%m"),
    "claim_count", float(total_claims), verdict,
)
```

### C-63 ダッシュボード — CARDS 追加

```python
{"system_id": "customer_claim_monthly", "metric": "claim_count",
 "title": "月次クレーム総数", "fmt": lambda v: f"{int(v)}件"}
```

---

## 10. テスト方針（test_analyze.py）

8テスト（TDD）:

| テスト名 | 内容 |
|---------|------|
| `test_verdict_good` | avg ≤ 5.0 → "good" |
| `test_verdict_warning` | 5.0 < avg ≤ 15.0 → "warning" |
| `test_verdict_alert` | avg > 15.0 → "alert" |
| `test_verdict_warning_upper_boundary` | avg = 15.0 → "warning"（上限境界値）|
| `test_total_claims` | count 合計の正確性 |
| `test_top_category` | 最多原因分類の特定 |
| `test_worst_customer` | 最多クレーム顧客の特定 |
| `test_missing_column_raises` | 必須列なし → ValueError |

---

## 11. catalog.yml エントリ

```yaml
- id: "C-74"
  name: "顧客クレーム件数・原因分類 月次集計"
  industry: "製造"
  department: "品質保証"
  difficulty: "★★★"
  status: "production-ready"
  priority: "A"
  path: "02_manufacturing/20_customer_claim_monthly"
  demo: "streamlit run 02_manufacturing/20_customer_claim_monthly/app.py"
  description: |
    顧客別・原因分類別のクレーム件数を CSV でアップロードし、月次推移と原因分類内訳を自動集計。
    月次平均クレーム数 ≤ 5件 → "good" の明快な verdict 設計。
    月次トレンドグラフと原因分類横棒グラフで改善ポイントを可視化。
```

---

## 12. スコープ外（将来対応）

- クレーム重篤度（S/A/B ランク）別の加重集計
- 顧客別トレンド自動アラート（前月比増加率）
- C-68 仕入先スコアリングとのクレーム指標統合

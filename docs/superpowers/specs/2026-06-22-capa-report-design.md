# CAPA 完了率・期限遵守率レポート 設計仕様書

**作成日:** 2026-06-22
**システムID:** C-76
**難易度:** ★★★
**カテゴリ:** 製造業 / 品質保証（QA）

---

## 1. 概要

月次の CAPA（是正・予防処置）実績（登録件数・完了件数・期限内完了件数）を CSV でアップロードし、
完了率と期限遵守率を自動算出して月次トレンドを可視化する。
完了率 ≥ 90% → "good" の明快な verdict 設計（高いほど良い）で、
結果を quality.db に書き込んで C-63 統合ダッシュボードに連携する。

---

## 2. 入力データ仕様

### CSV フォーマット（Wide 4列・1行=1ヶ月）

```csv
month,total,completed,on_time_completed
2024-01,12,10,9
2024-02,15,13,11
2024-03,10,8,8
```

- `month`: 年月（YYYY-MM 形式）
- `total`: 当月 CAPA 登録件数（正の整数）
- `completed`: 完了件数（0以上、total 以下）
- `on_time_completed`: 期限内完了件数（0以上、completed 以下）
- 最低構成: n ≥ 1

---

## 3. ファイル構成

```text
02_manufacturing/22_capa_report/
├── app.py           # Streamlit UI + DB 統合
├── analyze.py       # 完了率・期限遵守率集計ロジック（純粋関数）
├── visualize.py     # Plotly 折れ線トレンド + 月次件数積み上げ棒
├── sample_data.py   # デモ CSV 生成（6ヶ月）
├── STATUS.md
└── tests/
    ├── __init__.py
    └── test_analyze.py   # 8テスト（TDD）
```

---

## 4. データフロー

```text
CSV（month, total, completed, on_time_completed）
  └─ app.py
       └─ analyze.py: run_analysis() → 完了率 + 期限遵守率 + verdict
            ├─ visualize.py: rate_trend_chart() + monthly_bar_chart()
            └─ _common/db_writer.py: write_kpi("capa_report", ..., "completion_rate", rate, verdict)
                  └─ C-63 dashboard: capa_report カード追加
```

---

## 5. analyze.py — 計算ロジック

### 必須列

```python
REQUIRED_COLS = ["month", "total", "completed", "on_time_completed"]
```

### 処理フロー

1. 必須列の存在確認 → なければ ValueError
2. `total`, `completed`, `on_time_completed` を `pd.to_numeric(errors="coerce")` で変換 + NaN 行 `dropna()`
3. `total <= 0` の行を除外
4. n < 1 で ValueError（"有効なデータがありません"）
5. `total_capas = int(data["total"].sum())`
6. `avg_monthly_capas = total_capas / n_months`
7. `completion_rate = data["completed"].sum() / data["total"].sum() * 100`
8. `ontime_rate = data["on_time_completed"].sum() / data["total"].sum() * 100`
9. `open_count = int(data["total"].sum() - data["completed"].sum())`
10. verdict 判定

### verdict 基準（高いほど good）

| 条件 | verdict | 意味 |
|------|---------|------|
| completion_rate ≥ 90.0 | `"good"` | CAPA 管理良好 |
| completion_rate ≥ 70.0 | `"warning"` | 要注意 |
| completion_rate < 70.0 | `"alert"` | 要改善 |

### シグネチャ

```python
def run_analysis(df: pd.DataFrame) -> dict:
```

### 出力 dict（7キー）

```python
{
    "result_df":          pd.DataFrame,  # クレンジング済みデータ
    "total_capas":        int,           # 全期間 CAPA 合計
    "avg_monthly_capas":  float,         # 月次平均件数
    "completion_rate":    float,         # 完了率（%）
    "ontime_rate":        float,         # 期限遵守率（%）
    "open_count":         int,           # 未完了件数
    "verdict":            str,           # "good" | "warning" | "alert"
}
```

---

## 6. visualize.py — Plotly チャート

### rate_trend_chart(result_df) → go.Figure

- 完了率 + 期限遵守率の折れ線グラフ（`mode="lines+markers"`）
- x 軸: month / トレース: completion_rate（blue）/ ontime_rate（teal）
- 行ごとに rate を計算: `completed/total*100`, `on_time_completed/total*100`
- しきい値横線:
  - `add_hline(y=90.0, line_dash="dash", line_color="#16a34a")` — good ライン
  - `add_hline(y=70.0, line_dash="dash", line_color="#dc2626")` — alert ライン
- タイトル: "CAPA 完了率・期限遵守率 月次推移"
- 高さ: 380px、BG: `#f5f7fa`

### monthly_bar_chart(result_df) → go.Figure

- 月次 CAPA 件数の積み上げ棒グラフ（完了=green / 未完了=red）
- 完了: `completed` / 未完了: `total - completed`
- タイトル: "月次 CAPA 件数（完了 / 未完了）"
- 高さ: 320px、BG: `#f5f7fa`

---

## 7. sample_data.py — デモ用サンプルデータ

```
6ヶ月（2024-01〜2024-06）= 6行

設定:
- total: 10〜15件/月
- completion_rate: 月平均 ≈ 82% → verdict = "warning"
- ontime_rate: 月平均 ≈ 72%
```

列構成: `month`, `total`, `completed`, `on_time_completed`

---

## 8. app.py — UI レイアウト

### KPI 4列

| 列 | 表示内容 |
|----|---------|
| c1 | 月次平均 CAPA 件数（`{avg:.1f}件`）|
| c2 | 完了率（`{completion_rate:.1f}%`）|
| c3 | 期限遵守率（`{ontime_rate:.1f}%`）|
| c4 | verdict カード（good/warning/alert 色付き）|

### verdict ラベル

```python
_LABEL = {"good": "CAPA管理良好", "warning": "要注意", "alert": "要改善"}
_COLOR = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
```

---

## 9. DB 統合

```python
write_kpi(uid, "capa_report", datetime.now().strftime("%Y-%m"),
          "completion_rate", float(completion_rate), verdict)
```

### C-63 ダッシュボード — CARDS 追加

```python
{"system_id": "capa_report", "metric": "completion_rate",
 "title": "CAPA完了率", "fmt": lambda v: f"{v:.1f}%"}
```

---

## 10. テスト方針（test_analyze.py）

8テスト（TDD）:

| テスト名 | 内容 |
|---------|------|
| `test_verdict_good` | rate = 90.0 → "good"（境界値）|
| `test_verdict_warning` | rate = 80.0 → "warning" |
| `test_verdict_alert` | rate = 60.0 → "alert" |
| `test_verdict_warning_lower_boundary` | rate = 70.0 → "warning"（下限境界値）|
| `test_total_capas` | total 合計の正確性 |
| `test_completion_rate` | 複数月での完了率計算 |
| `test_open_count` | 未完了件数（total - completed）|
| `test_missing_column_raises` | 必須列なし → ValueError |

---

## 11. catalog.yml エントリ

```yaml
- id: "C-76"
  name: "CAPA完了率・期限遵守率レポート"
  industry: "製造"
  department: "品質保証"
  difficulty: "★★★"
  status: "production-ready"
  priority: "A"
  path: "02_manufacturing/22_capa_report"
  demo: "streamlit run 02_manufacturing/22_capa_report/app.py"
  description: |
    月次の CAPA 実績（登録・完了・期限内完了）を CSV でアップロードし、
    完了率と期限遵守率を自動算出。完了率 ≥ 90% → "good" の高いほど良い verdict 設計。
    折れ線トレンドと月次件数積み上げ棒グラフで改善ポイントを可視化。
```

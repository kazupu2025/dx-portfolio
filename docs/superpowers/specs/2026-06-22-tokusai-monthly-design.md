# 特採件数・理由別集計・月次推移 設計仕様書

**作成日:** 2026-06-22
**システムID:** C-77
**難易度:** ★★★
**カテゴリ:** 製造業 / 品質保証（QA）

---

## 1. 概要

月次の特採（特別採用）件数を理由別に CSV でアップロードし、月次推移と理由別内訳を自動集計する。
月次平均件数 ≤ 3件 → "good" の明快な verdict 設計で、結果を quality.db に書き込んで C-63 統合ダッシュボードに連携する。

---

## 2. 入力データ仕様

### CSV フォーマット（Long 3列・1行=1月×1理由）

```csv
month,reason,count
2024-01,寸法軽微逸脱,3
2024-01,外観不良,2
2024-01,機能上問題なし,1
2024-02,寸法軽微逸脱,4
```

- `month`: 年月（YYYY-MM 形式）
- `reason`: 理由分類（文字列）
- `count`: 件数（0以上の整数）
- 最低構成: n ≥ 1

---

## 3. ファイル構成

```text
02_manufacturing/23_tokusai_monthly/
├── app.py
├── analyze.py
├── visualize.py
├── sample_data.py
├── STATUS.md
└── tests/
    ├── __init__.py
    └── test_analyze.py
```

---

## 4. analyze.py — 計算ロジック

### 必須列

```python
REQUIRED_COLS = ["month", "reason", "count"]
```

### 処理フロー

1. 必須列確認 → なければ ValueError
2. `count` を `pd.to_numeric(errors="coerce")` + dropna + `count >= 0` フィルタ
3. n < 1 で ValueError
4. `total_count = int(data["count"].sum())`
5. `avg_monthly_count = total_count / n_months`
6. `top_reason`: reason ごとの count 合計が最大のもの
7. verdict 判定

### verdict 基準

| 条件 | verdict |
|------|---------|
| avg_monthly_count ≤ 3.0 | `"good"` |
| avg_monthly_count ≤ 10.0 | `"warning"` |
| avg_monthly_count > 10.0 | `"alert"` |

### 出力 dict（6キー）

```python
{
    "result_df":          pd.DataFrame,
    "total_count":        int,
    "avg_monthly_count":  float,
    "top_reason":         str,
    "n_reasons":          int,
    "verdict":            str,
}
```

---

## 5. visualize.py

### trend_chart(result_df) → go.Figure

- 理由別 月次件数の積み上げ棒グラフ（`barmode="stack"`）
- hline: y=10.0（alert/#dc2626）/ y=3.0（good/#16a34a）
- タイトル: "特採件数 月次推移（理由別）"

### reason_bar_chart(result_df) → go.Figure

- 理由別総件数 横棒グラフ（降順、navy=#1e3a5f）
- テキスト: 件数を棒の外側
- タイトル: "理由別 特採件数"

---

## 6. app.py KPI 4列

| 列 | 表示内容 |
|----|---------|
| c1 | 月次平均件数（`{avg:.1f}件`）|
| c2 | 最多理由（`{top_reason}`）|
| c3 | 理由分類数（`{n_reasons}種`）|
| c4 | verdict カード |

`_LABEL = {"good": "特採少", "warning": "要注意", "alert": "要改善"}`

---

## 7. DB 統合

```python
write_kpi(uid, "tokusai_monthly", datetime.now().strftime("%Y-%m"),
          "count", float(avg_monthly_count), verdict)
```

CARDS:
```python
{"system_id": "tokusai_monthly", "metric": "count",
 "title": "特採月次平均", "fmt": lambda v: f"{v:.1f}件"}
```

---

## 8. テスト（8テスト）

| テスト名 | 内容 |
|---------|------|
| `test_verdict_good` | avg=3.0 → "good"（境界値）|
| `test_verdict_warning` | avg=7.0 → "warning" |
| `test_verdict_alert` | avg=15.0 → "alert" |
| `test_verdict_warning_upper_boundary` | avg=10.0 → "warning"（上限境界値）|
| `test_total_count` | count 合計の正確性 |
| `test_top_reason` | 最多理由の特定 |
| `test_n_reasons` | 理由分類数のカウント |
| `test_missing_column_raises` | 必須列なし → ValueError |

---

## 9. sample_data

5理由 × 6ヶ月 = 30行
avg_monthly ≈ 7件 → verdict = "warning"
top_reason: 寸法軽微逸脱

---

## 10. catalog.yml

```yaml
- id: "C-77"
  name: "特採件数・理由別集計・月次推移"
  industry: "製造"
  department: "品質保証"
  difficulty: "★★★"
  status: "production-ready"
  priority: "A"
  path: "02_manufacturing/23_tokusai_monthly"
  demo: "streamlit run 02_manufacturing/23_tokusai_monthly/app.py"
  description: |
    月次の特採件数を理由別に集計し、月次推移と理由別内訳を自動集計。
    月次平均 ≤ 3件 → "good" の明快な verdict 設計。
    積み上げ棒グラフと理由別横棒グラフで改善ポイントを可視化。
```

# 4M変更台帳 集計・変更種別推移 設計仕様書

**作成日:** 2026-06-22 / **システムID:** C-78 / **難易度:** ★★★

## CSV フォーマット（3列 Long形式）
```csv
month,change_type,count
2024-01,人員変更,3
2024-01,設備変更,2
```
- change_type: 人員変更 / 設備変更 / 材料変更 / 方法変更

## analyze.py — 出力（6キー）
- result_df, total_count, avg_monthly_count, top_change_type, n_types, verdict
- verdict: avg ≤ 5.0→good / ≤ 15.0→warning / >15.0→alert

## visualize.py
- trend_chart: 変更種別 積み上げ棒グラフ（hline 5/15）
- type_bar_chart: 変更種別横棒グラフ（降順）

## app.py KPI 4列
月次平均件数 / 最多変更種別 / 変更種別数 / verdict
`_LABEL = {"good": "変更少", "warning": "要注意", "alert": "要改善"}`

## DB / CARDS
`write_kpi(..., "4m_change", "count", float(avg_monthly_count), verdict)`
`{"system_id": "4m_change", "metric": "count", "title": "4M変更月次平均", "fmt": lambda v: f"{v:.1f}件"}`

## sample_data
4変更種別 × 6ヶ月 = 24行、avg ≈ 8件/月 → warning、top=設備変更

## テスト（8テスト）
good(5.0) / warning(8.0) / alert(20.0) / warning_upper(15.0) /
total_count / top_change_type / n_types / missing_column_raises

## catalog.yml
id: C-78 / path: 02_manufacturing/24_4m_change / difficulty: ★★★

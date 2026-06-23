---
name: C-101 出荷検査合否率・保留件数 週次レポート
industry: 製造業
department: 品質管理
status: production-ready
priority: A
value: high
difficulty: ★★★
created: 2024-06-23
last_updated: 2024-06-23
description: >
  出荷検査の合否率と保留件数を週次で分析・可視化するダッシュボード。
  合格率の推移、製品別合格率、保留ロット数を追跡し、品質トレンドを把握します。
agents:
  - analyzer
input_files:
  - "sample_shipping_inspection.csv（日付・製品・ロットID・合否結果・保留フラグ）"
output_files:
  - "合格率、保留件数のKPIカード"
  - "週次合格率推移グラフ"
  - "製品別合格率グラフ"
demo: streamlit run app.py
notes: "サンプルデータは2024-01-01〜01-30の30ロット。Streamlitで対話的に分析可能。"
---

## 変更履歴

| 日付 | 変更内容 | 担当 |
|------|---------|------|
| 2024-06-23 | 新規作成 | - |

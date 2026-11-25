---
name: SaaSメトリクスダッシュボード
industry: IT・SaaS
department: 経営管理・CS
status: production-ready
priority: B
value: high
difficulty: medium
created: 2026-06-24
last_updated: 2026-06-24
description: >
  MRR・チャーン率・LTV・CACなどのSaaS重要指標を月次で追跡・可視化するダッシュボード。
  12ヶ月のデータから成長トレンド、健全性診断、プラン別構成を分析。
agents:
  - analyzer
  - reporter
input_files:
  - "sample_saas_metrics.csv（月次×プラン別指標）"
output_files:
  - output/analysis_result.json
  - output/charts/*.png
demo: "streamlit run app.py"
notes: "LTV/CAC ≥3で健全、≥1で要注意、<1で危機状態と判定"
---

## 変更履歴

| 日付 | 変更内容 | 担当 |
|------|---------|------|
| 2026-06-24 | 新規作成・実装完了 | Claude |

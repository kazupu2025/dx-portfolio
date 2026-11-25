---
name: C-115 RevPAR・客室稼働率ダッシュボード
industry: ホテル・観光
department: 経営管理
status: production-ready
priority: A
value: high
difficulty: ★★☆
created: 2026-06-24
last_updated: 2026-06-24
description: >
  ホテル経営の重要指標である RevPAR（客室あたり平均収益）と稼働率を
  可視化するダッシュボード。月別・客室タイプ別のトレンド分析と
  KPI監視機能を備え、経営判断を支援します。
agents:
  - analyzer
input_files:
  - sample_revpar.csv
output_files:
  - output/analysis_result.json
  - output/charts/monthly_trend.png
  - output/charts/room_type_ranking.png
demo: streamlit run app.py
notes: >
  - 稼働率 ≥70% で「good」、≥55% で「warning」、<55% で「alert」と判定
  - ADR（平均客室単価）と RevPAR（客室あたり収益）を区別して管理
  - 客室タイプ別の収益性比較機能を搭載
---

## 変更履歴

| 日付 | 変更内容 | 担当 |
|------|---------|------|
| 2026-06-24 | 新規作成、production-ready 状態で完成 | Claude |

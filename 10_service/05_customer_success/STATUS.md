---
name: カスタマーサクセス指標ダッシュボード
industry: IT・SaaS
department: カスタマーサクセス
status: production-ready
priority: A
value: high
difficulty: medium
created: 2026-06-24
last_updated: 2026-06-24
description: >
  NPS・ヘルススコア・オンボーディング完了率・リスク顧客分析を統合したCSダッシュボード。
  50顧客のデータから健全性診断、プラン別比較、リスク顧客特定を自動化。
agents:
  - analyzer
  - reporter
input_files:
  - "sample_customer_success.csv（50顧客×10項目）"
output_files:
  - output/analysis_result.json
demo: "streamlit run app.py"
notes: "健全率≥60%→good, ≥40%→warning, <40%→alert で総合判定。ヘルススコア = ログイン40% + 機能30% - チケット20% + オンボーディング10%"
---

## 変更履歴

| 日付 | 変更内容 | 担当 |
|------|---------|------|
| 2026-06-24 | 新規作成・実装完了 | Claude |

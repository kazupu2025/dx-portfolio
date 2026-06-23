---
name: C-125 顧客車検リマインダー・定期点検管理
industry: 自動車・整備業
department: 顧客サービス・営業
status: production-ready
# idea / designing / poc / tested / production-ready / deployed
priority: A
# A（高価値×低難易度）/ B（高価値×高難易度）/ C（その他）
value: high
# low / medium / high
difficulty: ★★☆
# low / medium / high
created: 2026-06-24
last_updated: 2026-06-24
description: >
  顧客の車検期限・オイル交換推奨日を自動判定し、
  期限切れ・30日以内・60日以内の3段階アラートで営業支援するシステム
agents:
  - cleaner
  - reporter
input_files:
  - "sample_customers.csv（顧客名・電話番号・最終車検日・走行距離など）"
output_files:
  - output/cleaned_customers.csv
  - output/analysis_report.md
demo: streamlit run app.py
notes: "基準日（pd.Timestamp.today()）から30日以内≤10件でGood、≤3件でAlert"
---

## 変更履歴

| 日付 | 変更内容 | 担当 |
|------|---------|------|
| {YYYY-MM-DD} | 新規作成 | - |

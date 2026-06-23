---
name: C-126 整備士別生産性・売上分析
industry: 自動車・整備業
department: 整備部門
status: production-ready
priority: A
value: high
difficulty: ★★☆
created: 2024-01-01
last_updated: 2026-06-24
description: >
  自動車整備業における整備士の生産性・売上・顧客満足度を多面的に分析し、
  人員配置最適化と報酬体系改善の意思決定を支援するシステム。
  整備士別の案件数・総売上・平均評価・時給効率を可視化し、
  パフォーマンス判定（GOOD/WARNING/ALERT）を自動生成。
agents:
  - cleaner
  - reporter
input_files:
  - "sample_mechanic.csv（整備履歴データ: 日付/整備士/サービス種別/労働時間/部品代/売上/評価）"
output_files:
  - "output/analysis_report.md"
  - "output/cleaned_mechanic.csv"
demo: streamlit run app.py
notes: >
  時給効率の判定基準:
  - GOOD: ≥¥6,000/時間
  - WARNING: ¥4,000-6,000/時間
  - ALERT: <¥4,000/時間
---

## 変更履歴

| 日付 | 変更内容 | 担当 |
|------|---------|------|
| 2026-06-24 | 新規作成（analyze.py/app.py/test_analyze.py） | claude-code |

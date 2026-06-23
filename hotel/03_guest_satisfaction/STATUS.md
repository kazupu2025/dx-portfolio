---
name: C-120 顧客満足度・リピート分析
industry: ホテル・観光
department: フロント・営業
status: production-ready
# idea / designing / poc / tested / production-ready / deployed
priority: A
# A（高価値×低難易度）/ B（高価値×高難易度）/ C（その他）
value: high
# low / medium / high
difficulty: medium
# low / medium / high
created: 2026-06-24
last_updated: 2026-06-24
description: >
  宿泊客の満足度データを分析し、総合スコア・リピート率・チャネル別満足度を可視化するシステム
agents:
  - analyzer
input_files:
  - "sample_guest_satisfaction.csv（50行）"
output_files:
  - output/analysis_report.md
  - output/result_analysis.json
demo: streamlit run app.py
notes: "総合スコア≥4.0→good, ≥3.5→warning, <3.5→alert"
---

## 変更履歴

| 日付 | 変更内容 | 担当 |
|------|---------|------|
| 2026-06-24 | 新規作成 | - |

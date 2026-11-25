---
name: C-119 宴会・イベント収益管理
industry: ホテル・観光
department: 宴会部門
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
  ホテルの宴会・イベント収益を分析・可視化。イベント種別・会場別の売上分析、
  月次トレンド、キャンセル率、1名単価などのKPIを算出し、経営判断を支援。
agents:
  - cleaner
  - validator
  - reporter
input_files:
  - sample_banquet.csv
output_files:
  - output/cleaned_banquet.csv
  - output/analysis_report.md
  - output/charts/*.png
demo: streamlit run app.py
notes: ""
---

## 変更履歴

| 日付       | 変更内容 | 担当 |
|-----------|---------|------|
| 2026-06-24 | 新規作成 | -    |

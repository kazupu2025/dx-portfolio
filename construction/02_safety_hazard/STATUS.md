---
name: C-121 安全管理・ヒヤリハット集計
industry: 建設・ゼネコン
department: 安全管理部
status: production-ready
# idea / designing / poc / tested / production-ready / deployed
priority: A
# A（高価値×低難易度）/ B（高価値×高難易度）/ C（その他）
value: high
# low / medium / high
difficulty: low
# low / medium / high
created: 2026-06-24
last_updated: 2026-06-24
description: >
  建設プロジェクトのヒヤリハット・安全事案を集計・分析し、重大度別・カテゴリ別・プロジェクト別に可視化。
  未解決件数と解決率で安全管理の進捗を追跡します。
agents:
  - cleaner
  - reporter
input_files:
  - "sample_safety.csv"
output_files:
  - output/analysis_report.json
demo: streamlit run app.py
notes: "重大度判定: 重大≦0かつ解決率≥90%→good, 重大≦2かつ解決率≥70%→warning, その他→alert"
---

## 変更履歴

| 日付 | 変更内容 | 担当 |
|------|---------|------|
| 2026-06-24 | 新規作成 | claude |

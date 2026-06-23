---
name: C-112 出席率・成績推移レポート
industry: 教育・研修
department: 教育管理
status: production-ready
priority: B
value: high
difficulty: ★★☆
created: 2026-06-24
last_updated: 2026-06-24
description: >
  月別の出席率・成績推移を複数クラス・科目で追跡分析。
  クラス間・科目間の差異を可視化し、要注意クラス/科目を自動抽出。
input_files:
  - "sample_attendance_grade.csv（月別×クラス別×科目別の出席率・成績データ）"
output_files:
  - "output/cleaned_attendance_grade.csv"
  - "Streamlitダッシュボード（KPIカード・月次トレンド・クラス別ランキング・科目別散布図）"
demo: streamlit run app.py
notes: |
  - 出席率と成績の相関分析を自動実施
  - A組（優秀）vs D組（要注意）の特性比較
  - 月次トレンドで改善/悪化を可視化
---

## 変更履歴

| 日付 | 変更内容 | 担当 |
|------|---------|------|
| 2026-06-24 | 新規作成 | Claude |

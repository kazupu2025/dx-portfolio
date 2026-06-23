---
name: C-116 工程進捗・原価差異レポート
industry: 建設・ゼネコン
department: 工程管理・経理
status: production-ready
priority: A
value: high
difficulty: ★★☆
created: 2026-06-24
last_updated: 2026-06-24
description: >
  10プロジェクト×3フェーズの工事実績から工期遅延と原価差異を自動分析。
  計画 vs 実績をガントチャート・原価差異グラフで可視化し、
  原価超過率≤5%→good の verdict で工事進捗管理を支援する。
agents:
  - analyze
input_files:
  - sample_progress_cost.csv（30行×10列）
output_files:
  - Streamlit Webアプリ（リアルタイム分析）
demo: streamlit run app.py
notes: |
  - 実績終了日がnull = 工事進行中
  - 開始遅延・終了遅延を自動計算
  - プロジェクト別・フェーズ別の詳細テーブル付き
---

## 変更履歴

| 日付 | 変更内容 | 担当 |
|------|---------|------|
| 2026-06-24 | 新規作成 | Claude |

---
name: C-122 資材コスト・発注管理
industry: 建設・ゼネコン
department: 資材・調達部門
status: production-ready
priority: A
value: high
difficulty: ★★☆
created: 2026-06-24
last_updated: 2026-06-24
description: >
  5プロジェクト×45件の資材発注データから月次コスト推移と仕入先別発注を自動分析。
  カテゴリ別コスト構成・単価変動率で資材コスト管理を支援する。
agents:
  - analyze
input_files:
  - sample_material.csv（45行×9列）
output_files:
  - Streamlit Webアプリ（リアルタイム分析）
demo: streamlit run app.py
notes: |
  - 月次コスト変動率 ≤10% → good, ≤20% → warning, >20% → alert
  - カテゴリ: 鉄鋼/コンクリート/木材/断熱・防水/建具・ガラス
  - プロジェクト別・仕入先別の詳細テーブル付き
---

## 変更履歴

| 日付 | 変更内容 | 担当 |
|------|---------|------|
| 2026-06-24 | 新規作成 | Claude |

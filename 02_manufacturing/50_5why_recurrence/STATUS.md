# C-104 なぜなぜ分析 原因カテゴリ別集計・再発率トレンド

- status: production-ready
- industry: 製造業
- difficulty: ★★★
- path: 02_manufacturing/50_5why_recurrence/

## 概要
なぜなぜ分析の結果をもとに、問題の根本原因を「設備不良」「作業ミス」「材料不良」「設計不良」「管理不備」の5つのカテゴリに分類し、各カテゴリの再発率をトレンド分析するシステム。

## 主要機能
- **カテゴリ別集計**: 根本原因カテゴリごとの件数と再発率
- **月次トレンド**: 月別再発率の時系列推移
- **KPI表示**: 全体再発率・再発件数・最多原因カテゴリ・総合判定
- **自動判定**: 再発率に基づく「良好/注意/警告」の3段階判定
  - 5%以下: 良好（✅）
  - 5%-15%: 注意（⚠️）
  - 15%以上: 警告（🚨）

## ファイル構成
- `sample_5why_recurrence.csv`: サンプルデータ（20件、2024年1月〜2月）
- `analyze.py`: コア分析ロジック
- `app.py`: Streamlit対話型UI
- `tests/test_analyze.py`: ユニットテスト（8件）

## 実行方法
```bash
cd 02_manufacturing/50_5why_recurrence
streamlit run app.py
```

## テスト実行
```bash
python -m pytest tests/test_analyze.py -v
```

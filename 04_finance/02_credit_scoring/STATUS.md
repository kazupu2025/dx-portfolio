# B-11 与信スコアリングデータ整備

| 項目 | 内容 |
|------|------|
| name | 与信スコアリングデータ整備 |
| industry | 金融・保険 |
| status | production-ready |
| path | 04_finance/02_credit_scoring |

## 概要

500件の申込データ（3スタイル混在CSV）にスコアカード方式の与信スコアを付与し、
高/中/低リスク分類・職業別分析・負債比率アラートを可視化する与信管理システム。

## 実装済みコンポーネント

- `_gen_sample_data.py` — 500申込者の架空データを3スタイルCSVに生成
- `output/cleanse.py` — 3スタイル統合・正規化・与信スコア算出（スコアカード方式）
- `output/validate.py` — クレンジング検証（18チェック、18/18 PASS）
- `output/analyze.py` — 6セクション分析レポート生成
- `output/validate_report.py` — レポート検証（7チェック、7/7 PASS）
- `output/visualize.py` — 3チャート生成（棒グラフ×2、ヒストグラム）
- `app.py` — Streamlit ダッシュボード
- `tests/` — pytest 25テスト（25/25 PASS）

## 起動方法

```bash
cd 04_finance/02_credit_scoring
# サンプルデータ生成（初回のみ）
python _gen_sample_data.py
# パイプライン実行
python output/cleanse.py
python output/analyze.py
python output/visualize.py
# テスト
python -m pytest tests/ -v
# ダッシュボード
streamlit run app.py
```

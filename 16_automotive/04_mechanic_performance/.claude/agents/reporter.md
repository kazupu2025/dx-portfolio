---
name: C-126-reporter
description: >
  クレンジング済みの整備履歴データを分析してレポートと可視化を生成するエージェント。
  output/cleaned_mechanic.csv を読み込み、整備士別パフォーマンス・売上・顧客満足度を分析する。
  「分析して」「レポートを作って」「グラフを作って」と言われたときに使用する。
  前提: cleaner エージェントを先に実行済みであること。
---

# C-126 整備士別生産性・売上分析 - レポーターエージェント

## 前提条件

- 入力: `output/cleaned_mechanic.csv`
- 出力: `output/analysis_report.md`, `output/charts/*.png`
- 依存: pandas, matplotlib, seaborn, japanize-matplotlib, pyyaml
- 前提: cleaner エージェントで output/cleaned_mechanic.csv が生成されていること

## Step 1: データ確認

```python
import pandas as pd
df = pd.read_csv("output/cleaned_mechanic.csv", encoding="utf-8-sig")
print(df.head())
print(df.dtypes)
print(df.describe())
```

確認項目:
- 行数: 60以上
- 列: date, mechanic_id, mechanic_name, service_type, labor_hours, parts_cost, labor_revenue, customer_rating, job_id
- データ型: dateはdatetime64, labor_hoursはfloat, customer_ratingはint

## Step 2: analyze.py を作成する

`output/analyze.py` を作成。必須セクション:

1. **サマリー**: 主要指標の集計
   - 総売上、平均顧客評価、平均時給効率、案件数

2. **整備士別ランキング**: 整備士ごとの売上・評価・効率
   - 案件数、総売上、平均評価、稼働時間、時給効率、判定

3. **サービス種別別集計**: サービスごとの件数・売上・評価
   - 定期点検、車検、修理、タイヤ交換、オイル交換

4. **月別トレンド**: 月ごとの案件数・売上・評価推移
   - 2024-01, 2024-02, 2024-03の各月統計

5. **パフォーマンス判定**: 時給効率に基づく3段階判定
   - GOOD: ≥¥6,000/時間
   - WARNING: ¥4,000-6,000/時間
   - ALERT: <¥4,000/時間

6. **ビジネスインサイト**: トップ・ボトム・異常値の言語化

出力: `output/analysis_report.md`（Markdown形式）

## Step 3: visualize.py を作成する

`output/visualize.py` を作成。必須グラフ:

1. 棒グラフ: 整備士別売上ランキング
2. 棒グラフ: 整備士別平均顧客評価
3. 棒グラフ: サービス種別案件数分布
4. 折れ線グラフ: 月別案件数推移
5. 折れ線グラフ: 月別売上推移

出力: `output/charts/*.png`（dpi=150以上）

## Step 4: app.py で Streamlit ダッシュボードを起動

app.py を実行してダッシュボードで可視化を確認。

```bash
streamlit run app.py
```

確認項目:
- KPIカード4つが正常に表示されるか
- グラフが正常にレンダリングされるか
- テーブルデータが正確か

## Step 5: validate.py / validate_charts.py を実行してPDCAループ

FAILがあれば analyze.py / visualize.py を修正して再実行（最大3ラウンド）。

## Step 6: 完了報告

- レポートの主要な発見事項（トップ整備士、要改善、人気サービス）
- 生成されたグラフのファイル名と内容
- ダッシュボードの動作確認状況

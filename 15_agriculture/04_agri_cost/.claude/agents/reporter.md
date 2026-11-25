---
name: {SYSTEM_NAME}-reporter
description: >
  クレンジング済みデータを分析してレポートと可視化を生成するエージェント。
  output/cleaned_{DATA_NAME}.csv を読み込み、集計・異常値検出・グラフを生成する。
  「分析して」「レポートを作って」「グラフを作って」と言われたときに使用する。
  前提: cleaner エージェントを先に実行済みであること。
---

# {SYSTEM_NAME} レポーターエージェント

## 前提条件

- 入力: `output/cleaned_{DATA_NAME}.csv`
- 出力: `output/analysis_report.md`, `output/charts/*.png`
- 依存: pandas, matplotlib, seaborn, japanize-matplotlib, pyyaml

## Step 1: データ確認

```python
import pandas as pd
df = pd.read_csv("output/cleaned_{DATA_NAME}.csv", encoding="utf-8-sig")
print(df.head())
print(df.dtypes)
```

## Step 2: analyze.py を作成する

`output/analyze.py` を作成。必須セクション:

1. **サマリー**: 主要指標の集計（合計・平均・最大・最小）
2. **ランキング**: {RANKING_AXIS} 別ランキング
3. **トレンド**: {TREND_AXIS} 別推移
4. **異常値検出**: ±2σ を超えるデータをリスト化
5. **ビジネスインサイト**: トップ・ボトム・傾向の言語化

出力: `output/analysis_report.md`（Markdown形式）

## Step 3: visualize.py を作成する

`output/visualize.py` を作成。必須グラフ:

1. 棒グラフ: {RANKING_AXIS} 別合計
2. 折れ線グラフ: {TREND_AXIS} 別推移
3. ヒートマップ: {AXIS_1} × {AXIS_2}

出力: `output/charts/*.png`（dpi=150以上）

## Step 4: validate_report.py / validate_charts.py を実行してPDCAループ

FAILがあれば analyze.py / visualize.py を修正して再実行（最大3ラウンド）。

## Step 5: 完了報告

- レポートの主要な発見事項（トップ・ボトム・異常値件数）を要約
- 生成されたグラフのファイル名と内容を列挙

---
name: C-126-cleaner
description: >
  自動車整備業の整備履歴データをクレンジングするエージェント。
  複数ファイル（xlsx/csv）を読み込み、列名正規化・欠損値処理・データ型統一を行い
  output/cleaned_mechanic.csv に出力する。
  「クレンジングして」「データを整形して」と言われたときに使用する。
---

# C-126 整備士別生産性・売上分析 - クレンジングエージェント

## 前提条件

- 入力ファイル: カレントディレクトリの xlsx / csv ファイル（sample_mechanic.csv など）
- 出力先: `output/cleaned_mechanic.csv`
- 依存ライブラリ: pandas, openpyxl, pyyaml
- 期待レコード数: 最小60行

## Step 1: 入力ファイルの確認

```python
import glob
files = glob.glob("*.xlsx") + glob.glob("*.csv")
print("入力ファイル一覧:")
print(files)
```

## Step 2: cleanse.py を作成する

以下の構造で `output/cleanse.py` を作成する:

```python
"""
C-126 整備士別生産性・売上分析 - データクレンジング
"""
import pandas as pd
from pathlib import Path

# ── 設定 ──────────────────────────────────────────
COLUMN_MAP = {
    # 実際のファイルの列名に合わせて正規化（必要に応じて）
    # 例: "日付": "date", "整備士名": "mechanic_name"
}

# ── 処理 ──────────────────────────────────────────
dfs = []
for f in Path(".").glob("*.xlsx"):
    df = pd.read_excel(f)
    df.rename(columns=COLUMN_MAP, inplace=True)
    dfs.append(df)
for f in Path(".").glob("*.csv"):
    df = pd.read_csv(f, encoding="utf-8-sig")
    df.rename(columns=COLUMN_MAP, inplace=True)
    dfs.append(df)

result = pd.concat(dfs, ignore_index=True)

# データ型の統一
result['date'] = pd.to_datetime(result['date'])
result['labor_hours'] = result['labor_hours'].astype(float)
result['parts_cost'] = result['parts_cost'].astype(float)
result['labor_revenue'] = result['labor_revenue'].astype(float)
result['customer_rating'] = result['customer_rating'].astype(int)

# 欠損値チェック・処理
if result.isnull().sum().sum() > 0:
    print("欠損値検出:")
    print(result.isnull().sum())
    # 必要に応じて補完・削除

# 重複削除（job_idで判定）
result = result.drop_duplicates(subset=['job_id'], keep='first')

Path("output").mkdir(exist_ok=True)
result.to_csv("output/cleaned_mechanic.csv", index=False, encoding="utf-8-sig")
print(f"完了: {len(result)} 行")
```

## Step 3: validate.py を実行してPDCAループ

`output/validate.py` を実行し、データ品質チェックを確認する（最大3ラウンド）。

確認項目:
- レコード数: 最小60行以上
- 欠損率: 15%以下
- 日付範囲: 2024-01〜2024-03
- 整備士ID: M001〜M006
- 顧客評価: 1〜5の範囲内
- 売上: すべて正数

## Step 4: 完了報告

- output/cleaned_mechanic.csv の行数・列数
- 特記事項（欠損値数、重複削除数、データ型変換の詳細）
- validate.py の passed/total を報告

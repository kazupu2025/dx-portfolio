---
name: {SYSTEM_NAME}-cleaner
description: >
  {INDUSTRY}の{DEPARTMENT}データをクレンジングするエージェント。
  複数ファイル（xlsx/csv）を読み込み、列名正規化・欠損値処理・フォーマット統一を行い
  output/cleaned_{DATA_NAME}.csv に出力する。
  「クレンジングして」「データを整形して」と言われたときに使用する。
---

# {SYSTEM_NAME} クレンジングエージェント

## 前提条件

- 入力ファイル: カレントディレクトリの xlsx / csv ファイル
- 出力先: `output/cleaned_{DATA_NAME}.csv`
- 依存ライブラリ: pandas, openpyxl, pyyaml

## Step 1: 入力ファイルの確認

```python
import glob
files = glob.glob("*.xlsx") + glob.glob("*.csv")
# ファイル一覧を表示して確認
```

## Step 2: cleanse.py を作成する

以下の構造で `output/cleanse.py` を作成する:

```python
"""
{SYSTEM_NAME} データクレンジング
"""
import pandas as pd
from pathlib import Path

# ── 設定 ──────────────────────────────────────────
COLUMN_MAP = {
    # {DATA_COLUMN_1}: "normalized_name_1",
    # {DATA_COLUMN_2}: "normalized_name_2",
    # 実際のファイルを確認して埋める
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
# 欠損値処理・型変換・重複削除をここに追加

Path("output").mkdir(exist_ok=True)
result.to_csv("output/cleaned_{DATA_NAME}.csv", index=False, encoding="utf-8-sig")
print(f"完了: {len(result)} 行")
```

## Step 3: validate.py を実行してPDCAループ

`output/validate.py` を実行し、`output/result.json` の `all_passed` が `true` になるまで
cleanse.py を修正して再実行する（最大3ラウンド）。

## Step 4: 完了報告

- output/cleaned_{DATA_NAME}.csv の行数・列数を報告
- result.json の passed/total を報告
- 発見した特記事項（フォーマット差異・異常値等）を報告

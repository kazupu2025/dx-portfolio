---
name: SaaSメトリクスダッシュボード-analyzer
description: >
  SaaS指標データを読み込み、MRR・チャーン率・LTV・CAC・健全性判定を計算するエージェント。
  analyze.py の計算結果を output/analysis_result.json に出力する。
  「分析して」「指標を計算して」と言われたときに使用する。
---

# SaaSメトリクスダッシュボード 分析エージェント

## 前提条件

- 入力ファイル: カレントディレクトリの sample_saas_metrics.csv（または CSV）
- 必須列: month, plan, new_customers, churned_customers, total_customers, mrr, new_mrr, churned_mrr, cac_spend
- 出力先: `output/analysis_result.json`
- 依存ライブラリ: pandas, numpy

## Step 1: 入力ファイルの確認

```bash
python -c "import pandas as pd; df = pd.read_csv('sample_saas_metrics.csv'); print(df.head()); print(df.info())"
```

## Step 2: analyze.py で分析を実行

```python
from analyze import analyze
import pandas as pd
import json
from pathlib import Path

# CSV を読み込み
df = pd.read_csv("sample_saas_metrics.csv")

# 分析実行
result = analyze(df)

# JSON に出力
Path("output").mkdir(exist_ok=True)
with open("output/analysis_result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False, default=str)

print("分析完了:")
print(f"  最新MRR: ¥{result['latest_mrr']:,.0f}")
print(f"  平均チャーン率: {result['avg_churn']:.1f}%")
print(f"  平均CAC: ¥{result['avg_cac']:,.0f}")
print(f"  平均LTV: ¥{result['avg_ltv']:,.0f}")
print(f"  LTV/CAC比: {result['ltv_cac_ratio']:.2f}")
print(f"  判定: {result['verdict']}")
```

## Step 3: テストを実行

```bash
python -m pytest tests/test_analyze.py -v
```

すべてのテストが PASSED になることを確認する（8テスト）。

## Step 4: 完了報告

- output/analysis_result.json の作成確認
- KPI値（MRR、チャーン率、CAC、LTV、LTV/CAC比）を報告
- 判定結果（good/warning/alert）を報告
- テスト結果（8/8 PASSED）を報告

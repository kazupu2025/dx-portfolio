# C-97 品質コスト明細集計

## 概要
品質管理における4つのコスト（予防/評価/内部失敗/外部失敗）を月別に集計・分析するシステム。

## ステータス
- **status**: production-ready
- **industry**: 製造業
- **difficulty**: ★★★

## ファイル構成
```
43_quality_cost_detail/
├── sample_quality_cost.csv       # サンプルデータ（24行：6ヶ月×4カテゴリ）
├── analyze.py                     # 分析メイン処理
├── app.py                         # Streamlit UI
├── STATUS.md                      # このファイル
└── tests/
    └── test_analyze.py            # 8個のテストケース
```

## 機能説明

### 入力データ
- `month`: YYYY-MM形式（例：2024-01〜2024-06）
- `cost_category`: 4種のコスト分類
  - 予防コスト（Appraisal）
  - 評価コスト（Evaluation）
  - 内部失敗コスト（Internal Failure）
  - 外部失敗コスト（External Failure）
- `amount`: 金額（整数）

### 分析結果

#### カテゴリ別集計
各コスト分類の合計を計算。

#### 失敗コスト比率
```
failure_ratio = (内部失敗+外部失敗) / 総コスト × 100%
```

#### 判定基準
| 失敗比率 | 判定 | 意味 |
|---------|------|------|
| ≤30% | good | 良好 |
| 30%〜50% | warning | 注意 |
| >50% | alert | 要対応 |

#### 月別推移
4つのコスト分類を時系列で可視化。

### UI構成

#### サイドバー
- サンプルデータ読み込みボタン
- CSV手動アップロード

#### メインエリア
- **KPIカード**: 総コスト、失敗コスト比率、判定
- **円グラフ**: コスト配分の可視化
- **積み上げ棒グラフ**: 月別推移
- **データテーブル**: カテゴリ別集計と月別詳細

## テスト項目（8個）

```python
✓ test_returns_dict()           # 返り値が辞書か
✓ test_required_keys()          # 必須キーが全て存在するか
✓ test_verdict_good()           # failure_pct=15→verdict="good"
✓ test_verdict_warning()        # failure_pct=40→verdict="warning"
✓ test_verdict_alert()          # failure_pct=60→verdict="alert"
✓ test_failure_ratio_range()    # 比率が0〜100%の範囲か
✓ test_total_cost_positive()    # 総コストが正数か
✓ test_category_df_not_empty()  # カテゴリデータが存在するか
```

## 実装日
2026-06-23

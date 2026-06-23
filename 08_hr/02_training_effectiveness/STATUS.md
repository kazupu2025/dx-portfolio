# C-111 研修効果測定レポート

## 概要

企業研修の効果を数値化し、研修投資のROIを測定する分析システム。

## 仕様

- **status**: production-ready
- **industry**: 人事・採用
- **difficulty**: ★★☆
- **path**: 08_hr/02_training_effectiveness/

## 機能

### 入力
- sample_training.csv（30行×9列）
  - employee_id: E001〜E015
  - name: 日本人名15名
  - department: 営業/製造/総務/IT/経理 の5部署
  - training_name: ビジネスマナー研修/Excel基礎/安全衛生/リーダーシップ/IT基礎 の5種
  - training_date: 2024-01-15〜2024-03-30
  - pre_score: 40〜75（研修前スコア、100点満点）
  - post_score: 60〜95（研修後スコア、pre_scoreより高い）
  - training_cost: 10000〜80000（円）
  - training_hours: 4〜24

### 分析ロジック（analyze.py）
- スコア改善 = post_score - pre_score
- 改善率 = (スコア改善 / pre_score) × 100%
- 1人あたりコスト = training_cost / スコア改善
- 費用対効果 = 平均改善 / (総費用 / 参加者数) × 1000

### KPI計算
- 平均スコア改善
- 改善率（平均）
- 総研修費用
- 総合評価（verdict）

### Verdict ロジック
- avg_improvement ≥ 15 → "good"（高い効果）
- avg_improvement ≥ 8 → "warning"（中程度）
- avg_improvement < 8 → "alert"（低い効果）

### 出力（Streamlit UI）
- KPIカード4つ: 平均スコア改善・改善率・総研修費用・判定
- 研修別効果ランキング棒グラフ
- 研修前後スコア比較grouped棒グラフ
- 部署別効果棒グラフ
- 費用対効果テーブル
- 詳細データ表示

## テスト

8個のテストで以下を検証：
1. 戻り値がdictであることを確認
2. 必要なキーが全て存在
3. verdict="good" (improvement=20)
4. verdict="warning" (improvement=10)
5. verdict="alert" (improvement=5)
6. 改善値がpositive
7. 参加者数カウント
8. 研修別効果dataframeが空でない

```bash
python -m pytest 08_hr/02_training_effectiveness/tests/ -v
```

## ファイル構成

```
08_hr/02_training_effectiveness/
├── sample_training.csv       # サンプルデータ（30行）
├── analyze.py                # 分析ロジック（REQUIRED_COLUMNS チェック含む）
├── app.py                    # Streamlit UI
├── STATUS.md                 # このファイル
└── tests/
    └── test_analyze.py       # 8個のテスト
```

## 実行方法

```bash
cd 08_hr/02_training_effectiveness

# テスト実行
python -m pytest tests/ -v

# Streamlit起動
streamlit run app.py
```

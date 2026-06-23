# C-109 多拠点リアルタイム品質比較ダッシュボード

## Status
- **status**: production-ready
- **industry**: 製造業
- **difficulty**: ★☆☆

## Overview
複数拠点の品質KPIを一画面で横断比較し、ベンチマーク・ランキング・トレンドを表示するダッシュボード。
マルチテナントDBの代わりに「site列付きCSV + SQLite集計」で多拠点比較を実現。

## File Structure
```
02_manufacturing/55_multisite_quality/
├── analyze.py                    # 分析ロジック
├── app.py                        # Streamlit アプリケーション
├── sample_multisite_quality.csv  # サンプルデータ（48行：4拠点×12ヶ月）
├── tests/
│   └── test_analyze.py          # 8つの単体テスト
└── STATUS.md                     # このファイル
```

## Key Features
- **サイドバー機能**:
  - CSVアップロード
  - サンプルデータ一括読み込み
  - 拠点フィルタ（multiselect）
  - KPIセレクタ（表示/非表示切り替え）

- **メインダッシュボード**:
  - KPIカード4つ（最優良拠点・最低拠点・平均不良率・判定）
  - 拠点ランキングテーブル（色分けされたスコア表示）
  - 拠点別KPI比較レーダーチャート
  - 月次不良率トレンド折れ線グラフ
  - 拠点別詳細KPI比較棒グラフ（4種類）

## Data Schema
### sample_multisite_quality.csv
| Column | Type | Range | Description |
|--------|------|-------|-------------|
| month | str | 2024-01〜2024-12 | 年月 |
| site | str | 東京工場/大阪工場/名古屋工場/福岡工場 | 拠点名 |
| defect_rate | float | 0.1〜3.0 | 不良率(%) |
| cpk | float | 0.8〜1.8 | 工程能力指数 |
| claim_count | int | 0〜15 | クレーム件数 |
| yield_rate | float | 95.0〜99.9 | 歩留まり率(%) |

## Scoring Algorithm
総合スコア（0-100）は以下の4指標の加重平均：
- 不良率の低さ: 25点
- Cpk指数の高さ: 25点
- クレーム件数の少なさ: 25点
- 歩留まり率の高さ: 25点

## Verdict Logic
| avg_defect | Verdict | Meaning |
|-----------|---------|---------|
| <= 0.5% | good | ✅ 良好 |
| 0.5〜1.5% | warning | ⚠️ 要注視 |
| > 1.5% | alert | 🔴 要改善 |

## Test Coverage
8つの単体テスト (`tests/test_analyze.py`)：
- 戻り値型チェック
- 必須キーの確認
- 3段階の判定ロジック検証
- サイト数の確認
- スコアソート順序の確認
- トレンドデータの存在確認

全テスト合格 ✅

## How to Run
```bash
# Streamlit アプリ起動
cd 02_manufacturing/55_multisite_quality
streamlit run app.py

# テスト実行
python -m pytest tests/ -v
```

## Sample Data Characteristics
- **東京工場**: 高品質（defect_rate低め、cpk高め）
- **大阪工場**: 中品質（標準レベル）
- **名古屋工場**: 中品質（標準レベル）
- **福岡工場**: 改善中（defect_rate高め）

## Implementation Notes
- Streamlit session_state でデータ永続化
- Plotly の dark template でモダンなUI
- レスポンシブレイアウト（st.columns）
- 大規模データセットもスムーズに処理

## Future Enhancements
- SQLite 統合（リアルタイム集計）
- 拠点追加機能（動的管理）
- カスタムしきい値設定
- エクスポート機能（PDF/Excel）
- ユーザー認証とロール管理

# C-118 整備案件・部品在庫管理ダッシュボード

自動車整備業向けの DX ダッシュボード。整備案件の売上管理と部品在庫の一元管理をサポート。

## ディレクトリ構成

```
automotive/01_service_inventory/
├── app.py                  # Streamlit ダッシュボード
├── analyze.py              # 分析エンジン
├── sample_service.csv      # サンプル整備案件データ (40行)
├── sample_parts.csv        # サンプル部品在庫データ (20行)
├── STATUS.md               # ステータス定義
├── README.md               # このファイル
└── tests/
    ├── __init__.py
    └── test_analyze.py     # 8つのユニットテスト
```

## 機能概要

### タブ1: 🔧 整備案件

**KPI カード**
- 総売上（全期間の売上合計）
- 案件完了率（完了案件数 / 全案件数 ％）
- 判定ステータス（good / warning / alert）
- 処理件数（全案件数と完了件数）

**グラフ**
- 整備タイプ別売上（棒グラフ）
- 月次売上トレンド（折れ線グラフ）

**テーブル**
- 案件一覧（ステータス別フィルタ対応）
- 統計情報（平均作業時間、平均部品代、平均売上、作業中件数）

### タブ2: 📦 部品在庫

**KPI カード**
- 在庫アラート件数（最小在庫未満の部品数）
- 管理部品数（全部品数）
- 平均在庫充足率

**グラフ**
- カテゴリ別在庫量（棒グラフ）

**テーブル**
- アラート部品一覧（赤ハイライト表示）
- 全在庫一覧（カテゴリフィルタ対応）

## データ仕様

### sample_service.csv

整備案件データ（40行）

| 列 | 型 | 例 |
|----|----|----|
| date | datetime | 2024-01-01 |
| job_id | string | J001 |
| customer | string | 顧客A |
| vehicle_type | string | 軽自動車/普通車/SUV/トラック |
| service_type | string | 定期点検/車検/修理/タイヤ交換/オイル交換 |
| labor_hours | float | 2.0 |
| parts_cost | int | 5000 |
| labor_rate | int | 8000（固定） |
| status | string | 完了/作業中/待機中 |

**計算項目**
- labor_cost = labor_hours × labor_rate
- total_revenue = labor_cost + parts_cost

### sample_parts.csv

部品在庫データ（20行）

| 列 | 型 | 例 |
|----|----|----|
| part_id | string | PR001 |
| part_name | string | エンジンオイル5L |
| category | string | オイル類/消耗品/タイヤ類/電装品 |
| current_stock | int | 25 |
| min_stock | int | 10 |
| unit_cost | int | 3500 |
| supplier | string | 仕入先A |

**計算項目**
- stock_ratio = current_stock / min_stock
- alert = current_stock < min_stock

## 分析エンジン (analyze.py)

### 集計結果

```python
result = analyze(service_df, parts_df)
```

返却値：

| キー | 型 | 説明 |
|------|----|----|
| service_df | DataFrame | 全整備案件（labor_cost, total_revenue計算済み） |
| service_type_df | DataFrame | 整備タイプ別集計 |
| vehicle_df | DataFrame | 車種別集計 |
| monthly_df | DataFrame | 月次売上集計 |
| parts_df | DataFrame | 全部品（stock_ratio, alert計算済み） |
| alert_parts | DataFrame | アラート部品（充足率昇順） |
| total_revenue | float | 総売上 |
| completion_rate | float | 完了率（%） |
| stock_alert_count | int | 在庫アラート件数 |
| verdict | str | 判定（good/warning/alert） |

### 判定ロジック

```python
if completion_rate >= 80 and stock_alert_count <= 2:
    verdict = "good"       # ✅ 良好
elif completion_rate >= 60:
    verdict = "warning"    # ⚠️ 要注意
else:
    verdict = "alert"      # 🔴 要改善
```

## テスト

### 実行方法

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio
python -m pytest automotive/01_service_inventory/tests/ -v
```

### テストケース（8項目）

| テスト | 説明 |
|-------|------|
| test_returns_dict | analyze() が dict を返す |
| test_required_keys | 必須キーが全て含まれている |
| test_verdict_good | 完了率 90%, アラート 1 件 → good |
| test_verdict_warning | 完了率 65%, アラート 5 件 → warning |
| test_completion_rate_range | 完了率が 0-100% の範囲内 |
| test_alert_parts_count | 在庫アラート件数の集計が正確 |
| test_total_revenue_positive | 総売上が正の値 |
| test_service_type_df_not_empty | 整備タイプ別集計が空でない |

## Streamlit アプリ実行

### 環境準備

```bash
# dx-portfolio ディレクトリで
pip install streamlit pandas numpy

# または
pip install -r requirements.txt
```

### 起動コマンド

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio
streamlit run automotive/01_service_inventory/app.py
```

ブラウザが自動で開きます（http://localhost:8501）

### UI機能

- **ステータスフィルタ**（タブ1）: 完了/作業中/待機中を選択
- **カテゴリフィルタ**（タブ2）: オイル類/消耗品/タイヤ類/電装品を選択
- **数値フォーマット**: 金額は ¥ 付きカンマ区切り、充足率は % 表示

## 実装詳細

### analyze.py

- pandas groupby による効率的な集計
- 売上計算（labor_cost + parts_cost）
- 完了率と在庫アラート判定
- 3段階ステータス判定（good/warning/alert）

### app.py

- Streamlit 2タブレイアウト
- DaisyUI スタイルの KPI カード
- Matplotlib / Plotly チャート
- 日付フォーマット自動化
- レスポンシブ列配置

## 拡張予定

- [ ] CSV インポート機能
- [ ] 部品の自動注文提案
- [ ] メール通知（アラート時）
- [ ] ダッシュボード pdf エクスポート
- [ ] 顧客別・車種別の詳細分析
- [ ] 過去期間比較機能

## ステータス

- Status: **production-ready**
- Industry: 自動車・整備業
- Difficulty: ★★☆（中程度）

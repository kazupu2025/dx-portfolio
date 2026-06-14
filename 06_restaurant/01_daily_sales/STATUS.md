# STATUS.md — A-02 飲食×日次売上・廃棄ロス集計レポート

| key | value |
|-----|-------|
| id | A-02 |
| name | 飲食×日次売上・廃棄ロス集計レポート |
| industry | 飲食 |
| status | production-ready |
| path | 06_restaurant/01_daily_sales |
| demo | `cd 06_restaurant/01_daily_sales && streamlit run app.py` |

## 概要

飲食店5店舗（渋谷・新宿・池袋・横浜・大阪）の日次売上CSVを集計し、
廃棄ロス率（廃棄額÷売上額）を算出。5%超の店舗をアラート表示する経営支援レポート。

## 実装済み機能

- マルチエージェントパイプライン（cleaner → data-analyst → data-viz-engineer）
- Streamlit Webアプリ（app.py）によるインタラクティブ可視化
- 廃棄ロス率アラート（5%閾値超過店舗の強調表示）
- 店舗別・日次売上集計レポート
- pytestによる自動テスト（tests/）
- PDCA自己修正ループ付きエージェント

## 起動方法

```bash
cd 06_restaurant/01_daily_sales
pip install -r requirements.txt
streamlit run app.py
```

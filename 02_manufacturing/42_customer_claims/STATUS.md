# C-96 顧客クレーム件数・原因分類 月次集計

- **status**: production-ready
- **industry**: 製造業
- **difficulty**: ★★★
- **path**: 02_manufacturing/42_customer_claims/

## 概要

月次ベースで顧客クレームの件数・原因分類を集計するシステム。
月平均件数に基づいて、システムの健全性を「good / warning / alert」の3段階で判定する。

## 機能

- クレーム件数の月次推移（折れ線グラフ）
- 原因カテゴリ別集計（棒グラフ）
- 顧客別集計（棒グラフ）
- 未完了件数の追跡
- 健全性判定（月平均件数ベース）

## ファイル構成

- `sample_customer_claims.csv` — 20行のサンプルデータ
- `analyze.py` — 分析エンジン（pandas）
- `tests/test_analyze.py` — 8つの単体テスト
- `app.py` — Streamlit UI

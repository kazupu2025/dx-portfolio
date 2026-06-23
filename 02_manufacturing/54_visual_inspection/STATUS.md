# C-108 AI外観検査自動判定

- **status**: production-ready
- **industry**: 製造業
- **difficulty**: ★☆☆
- **path**: 02_manufacturing/54_visual_inspection/
- **date_completed**: 2026-06-23

## 概要

Deep Learning なしで PIL + numpy のルールベース画像解析により外観検査を実現する自動判定システム。

## 検査対象

- 輝度（明るさの偏り） → 汚れ・変色検出
- エッジ密度（輪郭の多さ） → 傷・亀裂検出
- 色分散 → 色ムラ検出
- 暗領域率 → 穴・欠損検出

## ファイル構成

- `inspector.py` — コア検査ロジック（特徴量抽出・分類）
- `app.py` — Streamlit UI（画像アップロード・結果表示）
- `tests/test_analyze.py` — ユニットテスト（8つのテストケース）

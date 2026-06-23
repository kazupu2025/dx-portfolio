# C-106 市場品質フィードバックループ

## Project Information
- **system_id**: C-106
- **name**: 市場品質フィードバックループ
- **industry**: Manufacturing
- **difficulty**: ★☆☆
- **status**: production-ready
- **path**: `02_manufacturing/52_quality_feedback_loop/`

## Description
市場クレーム → 工程解析 → 改善策実施 → 効果確認 のフィードバックループを CSV データで管理・可視化するシステム。

## Key Features
- 市場クレームの工程別原因分析
- 改善策の効果測定（改善率）
- 改善リードタイム追跡
- 工程別・改善策別の効果ランキング
- フィードバックループ図の可視化

## Implementation Timeline
- Created: 2026-06-23
- Status: production-ready

## Files
- `analyze.py` — Core analysis logic
- `app.py` — Streamlit dashboard
- `sample_feedback_loop.csv` — Sample dataset (25 rows)
- `tests/test_analyze.py` — Unit tests (8 tests)

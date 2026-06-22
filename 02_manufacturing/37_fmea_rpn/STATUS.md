# C-91 FMEA RPN動的更新

- **name**: FMEA RPN動的更新（SQLite CRUD）
- **industry**: 製造
- **department**: 品質保証
- **status**: production-ready

## Overview

FMEA（故障モード影響解析）項目をSQLiteで管理し、重大度×発生頻度×検出難度からRPNを自動計算するシステム。
フォーム入力によるCRUD操作とリアルタイムRPN更新、分析チャートを提供します。

## Components

- **db.py** — SQLite CRUD操作（add, update, delete, get_all_items）
- **analyze.py** — RPN集計分析（avg_rpn, max_rpn, high_risk_count, verdict）
- **visualize.py** — Plotlyチャート（RPNバーチャート、リスクマップ散布図）
- **app.py** — Streamlit UI（一覧・新規登録・更新・削除タブ）

## Database

- **Path**: `02_manufacturing/37_fmea_rpn/fmea.db`
- **Tables**: `fmea_items`
- **Columns**: id, process_name, failure_mode, effect, severity, cause, occurrence, detection, rpn, current_control, action_required, created_at, updated_at

## Key Metrics

- **avg_rpn**: 平均RPN（1-1000）
- **max_rpn**: 最大RPN
- **high_risk_count**: RPN > 200件数
- **verdict**: avg_rpn ≤ 100 → "good" / ≤ 200 → "warning" / > 200 → "alert"

## Sample Data

初回起動時に5件のサンプルFMEAデータを自動投入します。

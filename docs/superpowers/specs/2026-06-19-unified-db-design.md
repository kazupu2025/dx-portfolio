# 統合品質DB + 横断ダッシュボード 設計仕様書

**作成日:** 2026-06-19
**難易度:** ★★☆
**カテゴリ:** 製造業 / 生産・品質（横断）

---

## 1. 概要

C-61（品質管理ポータル）と C-62（Cp/Cpk分析）の分析結果を共通 SQLite DB に蓄積し、全品質KPIを1画面で横断表示する統合ダッシュボードを構築する。

### 設計方針（アダプター追加・非破壊）

既存システムは一切変更しない。分析完了後に `_common/db_writer.py` を呼ぶだけでDBに書き込まれる。

```text
C-61 pipelines（既存変更なし）
  └── 分析後 → db_writer.py → quality.db（SQLite）

C-62 app.py（既存変更なし）
  └── 分析後 → db_writer.py → quality.db（SQLite）

quality.db
  └── unified_dashboard.py（新規 Streamlit app）
```

---

## 2. ファイル構成

```text
dx-portfolio/
├── _common/
│   ├── db_writer.py          # 全システム共通のDB書き込みモジュール
│   ├── validate_base.py      # （既存）
│   └── report_base.py        # （既存）
│
└── 02_manufacturing/
    └── 09_unified_dashboard/
        ├── dashboard.py       # Streamlit 横断ダッシュボード
        ├── db_reader.py       # DB読み込みクエリ集
        ├── STATUS.md
        └── tests/
            ├── test_db_writer.py
            └── test_db_reader.py
```

`quality.db` の保存先: `dx-portfolio/data/quality.db`（`.gitignore` 対象）

---

## 3. DBスキーマ（3テーブル）

### 3-1. uploads（書き込み記録）

```sql
CREATE TABLE IF NOT EXISTS uploads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    system_id   TEXT    NOT NULL,   -- 'defect_rate'|'claim'|'yield'|'inspector'|'lot'|'cpk'
    uploaded_at TEXT    NOT NULL,   -- ISO8601 UTC
    filename    TEXT,
    row_count   INTEGER
);
```

### 3-2. monthly_kpis（信号機カード＋トレンド用）

```sql
CREATE TABLE IF NOT EXISTS monthly_kpis (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id   INTEGER NOT NULL REFERENCES uploads(id),
    system_id   TEXT    NOT NULL,
    year_month  TEXT    NOT NULL,   -- 'YYYY-MM'
    category    TEXT,               -- ライン名・工程名など（省略可、NULLはサマリー）
    metric_name TEXT    NOT NULL,   -- 'defect_rate'|'claim_count'|'yield_rate'|...
    value       REAL    NOT NULL,
    verdict     TEXT    NOT NULL    -- 'good'|'warning'|'alert'
);
```

### 3-3. cpk_results（Cp/Cpk専用）

```sql
CREATE TABLE IF NOT EXISTS cpk_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id       INTEGER NOT NULL REFERENCES uploads(id),
    uploaded_at     TEXT    NOT NULL,
    process         TEXT    NOT NULL,
    n               INTEGER NOT NULL,
    mean            REAL    NOT NULL,
    std             REAL    NOT NULL,
    usl             REAL    NOT NULL,
    lsl             REAL    NOT NULL,
    cp              REAL    NOT NULL,
    cpk             REAL    NOT NULL,
    verdict         TEXT    NOT NULL,   -- 'good'|'warning'|'alert'
    out_of_spec_pct REAL    NOT NULL
);
```

verdict の変換: 非常に良好/良好 → `good`、要改善 → `warning`、不可 → `alert`

---

## 4. db_writer.py インターフェース

```python
# _common/db_writer.py

DB_PATH = Path(__file__).parent.parent / "data" / "quality.db"

def get_db() -> sqlite3.Connection:
    """シングルトン接続（autocommit=False）"""

def init_db() -> None:
    """テーブルが存在しなければ CREATE TABLE を実行"""

def write_upload(system_id: str, filename: str | None, row_count: int | None) -> int:
    """uploads に1行挿入し、生成された id を返す"""

def write_kpi(
    upload_id: int,
    system_id: str,
    year_month: str,
    metric_name: str,
    value: float,
    verdict: str,
    category: str | None = None,
) -> None:
    """monthly_kpis に1行挿入"""

def write_cpk_results(upload_id: int, results: list[dict]) -> None:
    """cpk_results に results の各要素を挿入（analyze.run_analysis の出力形式）"""
```

### 各システムからの呼び出しイメージ

**C-61 defect_rate パイプライン:**
```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from _common.db_writer import init_db, write_upload, write_kpi

init_db()
upload_id = write_upload("defect_rate", filename, row_count)
write_kpi(upload_id, "defect_rate", "2024-01", "defect_rate", 0.012, "good")
```

**C-62 app.py（分析実行ボタン後）:**
```python
from _common.db_writer import init_db, write_upload, write_cpk_results

init_db()
upload_id = write_upload("cpk", filename, len(df))
write_cpk_results(upload_id, results)   # results = run_analysis(...)の返り値
```

---

## 5. ダッシュボード設計（dashboard.py）

### 5-1. レイアウト

```text
┌─────────────────────────────────────────────────────┐
│  品質横断ダッシュボード          期間: [直近3ヶ月▾]  │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────┤
│  不良率  │ クレーム │  歩留り  │ 最悪Cpk  │受入不良率│ 特採件数 │
│  1.2%  ✓ │  12件  ✗ │  97.3% ✓ │  0.98  △ │  0.3%  ✓ │  5件   ✗ │
├──────────┴──────────┴──────────┴──────────┴──────────┴──────────┤
│  ▼ 選択KPIの推移（折れ線グラフ）                               │
│  [plotly line chart — 選択期間の月次推移]                       │
└─────────────────────────────────────────────────────────────────┘
```

### 5-2. 信号機カード定義（6枚）

| カード | system_id | metric_name | good | warning | alert |
|--------|-----------|-------------|------|---------|-------|
| 月次不良率 | `defect_rate` | `defect_rate` | <1% | <3% | ≥3% |
| クレーム件数 | `claim` | `claim_count` | <5件 | <10件 | ≥10件 |
| 歩留まり率 | `yield` | `yield_rate` | ≥98% | ≥95% | <95% |
| 最悪工程Cpk | `cpk` | `min_cpk` | ≥1.33 | ≥1.00 | <1.00 |
| 検査員不良検出率 | `inspector` | `avg_detection_rate` | ≥95% | ≥90% | <90% |
| ロット合否率 | `lot` | `pass_rate` | ≥98% | ≥95% | <95% |

カラー: good=#dcfce7（文字#16a34a）、warning=#fff7ed（文字#d97706）、alert=#fef2f2（文字#dc2626）

### 5-3. db_reader.py クエリ

```python
def get_latest_kpis(db: Connection) -> list[dict]:
    """各 system_id × metric_name の最新 year_month のレコードを1件ずつ取得"""

def get_kpi_trend(db: Connection, system_id: str, metric_name: str, months: int = 3) -> list[dict]:
    """指定 system_id の直近 N ヶ月分 monthly_kpis を返す（category=NULL のみ）"""

def get_latest_cpk(db: Connection) -> list[dict]:
    """最新 upload の cpk_results を全工程分返す"""
```

---

## 6. カラーテーマ（C-61/C-62 統一）

| 用途 | カラーコード |
|------|-------------|
| ヘッダー背景 | `#1e3a5f` |
| good | `#16a34a` / `#dcfce7` |
| warning | `#d97706` / `#fff7ed` |
| alert | `#dc2626` / `#fef2f2` |
| ページ背景 | `#f5f7fa` |

---

## 7. テスト方針

### test_db_writer.py（8テスト）

- `test_init_db_creates_tables` — 3テーブルが存在すること
- `test_write_upload_returns_id` — upload_id が正の整数であること
- `test_write_kpi_stored_correctly` — 書いた値が読み出せること
- `test_write_cpk_results_multiple` — 複数工程を一括書き込みできること
- `test_write_kpi_invalid_verdict_raises` — 不正な verdict で ValueError
- `test_idempotent_init_db` — 2回 init_db を呼んでもエラーなし
- `test_upload_id_foreign_key` — 存在しない upload_id で write_kpi が失敗すること
- `test_db_path_created_if_not_exists` — data/ ディレクトリがなくても自動作成

### test_db_reader.py（6テスト）

- `test_get_latest_kpis_returns_latest_per_system`
- `test_get_latest_kpis_empty_when_no_data`
- `test_get_kpi_trend_returns_n_months`
- `test_get_kpi_trend_category_null_only`
- `test_get_latest_cpk_returns_all_processes`
- `test_get_latest_cpk_empty_when_no_data`

---

## 8. スコープ外（将来対応）

- C-61 portal.py からの自動 DB 書き込み（現在はパイプライン手動実行後に呼ぶ）
- C-62 以外の ★★☆ システム（SPC管理図等）の db_writer 連携
- DB バックアップ / エクスポート機能
- 期間フィルターの拡張（カスタム日付範囲）

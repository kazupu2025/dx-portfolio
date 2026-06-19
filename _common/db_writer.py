"""全品質システム共通の SQLite 書き込みモジュール"""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "quality.db"

_VALID_VERDICTS = {"good", "warning", "alert"}

_DDL = """
CREATE TABLE IF NOT EXISTS uploads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    system_id   TEXT    NOT NULL,
    uploaded_at TEXT    NOT NULL,
    filename    TEXT,
    row_count   INTEGER
);
CREATE TABLE IF NOT EXISTS monthly_kpis (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id   INTEGER NOT NULL REFERENCES uploads(id),
    system_id   TEXT    NOT NULL,
    year_month  TEXT    NOT NULL,
    category    TEXT,
    metric_name TEXT    NOT NULL,
    value       REAL    NOT NULL,
    verdict     TEXT    NOT NULL
);
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
    verdict         TEXT    NOT NULL,
    out_of_spec_pct REAL    NOT NULL
);
"""


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """テーブルが存在しなければ作成する（冪等）"""
    conn = get_db()
    conn.executescript(_DDL)
    conn.commit()
    conn.close()


def write_upload(
    system_id: str,
    filename: str | None = None,
    row_count: int | None = None,
) -> int:
    """uploads に1行挿入し、生成された id を返す"""
    conn = get_db()
    uploaded_at = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT INTO uploads (system_id, uploaded_at, filename, row_count) VALUES (?, ?, ?, ?)",
        (system_id, uploaded_at, filename, row_count),
    )
    upload_id = cur.lastrowid
    conn.commit()
    conn.close()
    return upload_id


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
    if verdict not in _VALID_VERDICTS:
        raise ValueError(f"verdict は {_VALID_VERDICTS} のいずれかである必要があります。got: {verdict!r}")
    conn = get_db()
    conn.execute(
        """INSERT INTO monthly_kpis
           (upload_id, system_id, year_month, category, metric_name, value, verdict)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (upload_id, system_id, year_month, category, metric_name, value, verdict),
    )
    conn.commit()
    conn.close()


def _cpk_to_verdict(cpk: float) -> str:
    if cpk >= 1.33:
        return "good"
    if cpk >= 1.00:
        return "warning"
    return "alert"


def write_cpk_results(upload_id: int, results: list[dict]) -> None:
    """cpk_results に results の各要素を挿入（analyze.run_analysis の出力形式）"""
    uploaded_at = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    for r in results:
        conn.execute(
            """INSERT INTO cpk_results
               (upload_id, uploaded_at, process, n, mean, std,
                usl, lsl, cp, cpk, verdict, out_of_spec_pct)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                upload_id, uploaded_at,
                r["process"], r["n"], r["mean"], r["std"],
                r["usl"], r["lsl"], r["cp"], r["cpk"],
                _cpk_to_verdict(r["cpk"]),
                r["out_of_spec_pct"],
            ),
        )
    conn.commit()
    conn.close()

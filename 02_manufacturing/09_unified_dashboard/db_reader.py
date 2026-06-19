"""統合品質DB の読み込みクエリ集"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from _common.db_writer import get_db


def get_latest_kpis(conn: sqlite3.Connection | None = None) -> list[dict]:
    """各 system_id × metric_name の最新 year_month のサマリーKPIを返す"""
    close = conn is None
    if conn is None:
        conn = get_db()
    rows = conn.execute("""
        SELECT k.system_id, k.metric_name, k.year_month, k.value, k.verdict
        FROM monthly_kpis k
        INNER JOIN (
            SELECT system_id, metric_name, MAX(year_month) AS max_ym
            FROM monthly_kpis
            WHERE category IS NULL
            GROUP BY system_id, metric_name
        ) latest ON k.system_id = latest.system_id
                   AND k.metric_name = latest.metric_name
                   AND k.year_month = latest.max_ym
        WHERE k.category IS NULL
    """).fetchall()
    if close:
        conn.close()
    return [
        {
            "system_id": r[0],
            "metric_name": r[1],
            "year_month": r[2],
            "value": r[3],
            "verdict": r[4],
        }
        for r in rows
    ]


def get_kpi_trend(
    system_id: str,
    metric_name: str,
    months: int = 3,
    conn: sqlite3.Connection | None = None,
) -> list[dict]:
    """直近 N ヶ月分の月次KPI（category=NULL のサマリーのみ、新しい順）"""
    close = conn is None
    if conn is None:
        conn = get_db()
    rows = conn.execute(
        """SELECT year_month, value, verdict
           FROM monthly_kpis
           WHERE system_id = ? AND metric_name = ? AND category IS NULL
           ORDER BY year_month DESC
           LIMIT ?""",
        (system_id, metric_name, months),
    ).fetchall()
    if close:
        conn.close()
    return [{"year_month": r[0], "value": r[1], "verdict": r[2]} for r in rows]


def get_latest_cpk(conn: sqlite3.Connection | None = None) -> list[dict]:
    """最新アップロードの cpk_results を全工程分返す"""
    close = conn is None
    if conn is None:
        conn = get_db()
    row = conn.execute("SELECT MAX(upload_id) FROM cpk_results").fetchone()
    if row[0] is None:
        if close:
            conn.close()
        return []
    latest_id = row[0]
    rows = conn.execute(
        """SELECT process, n, mean, std, usl, lsl, cp, cpk, verdict, out_of_spec_pct
           FROM cpk_results WHERE upload_id = ?""",
        (latest_id,),
    ).fetchall()
    if close:
        conn.close()
    cols = ["process", "n", "mean", "std", "usl", "lsl", "cp", "cpk", "verdict", "out_of_spec_pct"]
    return [dict(zip(cols, r)) for r in rows]

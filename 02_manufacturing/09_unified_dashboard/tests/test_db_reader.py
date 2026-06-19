"""db_reader.py のテスト"""
import sqlite3
import pytest
from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent.parent))

from _common import db_writer
from db_reader import get_latest_kpis, get_kpi_trend, get_latest_cpk


@pytest.fixture
def conn(tmp_path, monkeypatch):
    """初期化済みの一時 DB 接続を返す"""
    db_path = tmp_path / "test_quality.db"
    monkeypatch.setattr(db_writer, "DB_PATH", db_path)
    db_writer.init_db()
    c = sqlite3.connect(db_path)
    c.execute("PRAGMA foreign_keys = ON")
    yield c
    c.close()


def _insert_kpi(conn, system_id, year_month, metric_name, value, verdict):
    conn.execute(
        "INSERT INTO uploads (system_id, uploaded_at) VALUES (?, '2024-01-01T00:00:00+00:00')",
        (system_id,),
    )
    uid = conn.execute("SELECT MAX(id) FROM uploads").fetchone()[0]
    conn.execute(
        """INSERT INTO monthly_kpis
           (upload_id, system_id, year_month, metric_name, value, verdict)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (uid, system_id, year_month, metric_name, value, verdict),
    )
    conn.commit()


def test_get_latest_kpis_returns_newest(conn):
    _insert_kpi(conn, "defect_rate", "2024-01", "defect_rate", 0.015, "warning")
    _insert_kpi(conn, "defect_rate", "2024-02", "defect_rate", 0.008, "good")
    rows = get_latest_kpis(conn)
    dr = next(r for r in rows if r["system_id"] == "defect_rate")
    assert dr["year_month"] == "2024-02"
    assert dr["value"] == pytest.approx(0.008)
    assert dr["verdict"] == "good"


def test_get_latest_kpis_empty_when_no_data(conn):
    assert get_latest_kpis(conn) == []


def test_get_latest_kpis_multiple_systems(conn):
    _insert_kpi(conn, "defect_rate", "2024-01", "defect_rate", 0.02, "warning")
    _insert_kpi(conn, "claim", "2024-01", "claim_count", 8, "warning")
    rows = get_latest_kpis(conn)
    assert len(rows) == 2
    assert {r["system_id"] for r in rows} == {"defect_rate", "claim"}


def test_get_kpi_trend_returns_n_months(conn):
    for ym, val in [("2024-01", 0.02), ("2024-02", 0.015),
                    ("2024-03", 0.01), ("2024-04", 0.008)]:
        _insert_kpi(conn, "defect_rate", ym, "defect_rate", val, "good")
    rows = get_kpi_trend("defect_rate", "defect_rate", months=3, conn=conn)
    assert len(rows) == 3
    assert rows[0]["year_month"] == "2024-04"  # 新しい順


def test_get_kpi_trend_excludes_category_rows(conn):
    """category が NULL でない行はトレンド集計に含まない"""
    conn.execute(
        "INSERT INTO uploads (system_id, uploaded_at) VALUES ('defect_rate', '2024-01-01T00:00:00+00:00')"
    )
    uid = conn.execute("SELECT MAX(id) FROM uploads").fetchone()[0]
    conn.execute(
        """INSERT INTO monthly_kpis
           (upload_id, system_id, year_month, category, metric_name, value, verdict)
           VALUES (?, 'defect_rate', '2024-01', 'L1', 'defect_rate', 0.02, 'good')""",
        (uid,),
    )
    conn.commit()
    rows = get_kpi_trend("defect_rate", "defect_rate", months=3, conn=conn)
    assert rows == []


def test_get_latest_cpk_returns_all_processes(conn):
    conn.execute(
        "INSERT INTO uploads (system_id, uploaded_at) VALUES ('cpk', '2024-01-01T00:00:00+00:00')"
    )
    uid = conn.execute("SELECT MAX(id) FROM uploads").fetchone()[0]
    for proc in ["溶接", "塗装", "組立"]:
        conn.execute(
            """INSERT INTO cpk_results
               (upload_id, uploaded_at, process, n, mean, std,
                usl, lsl, cp, cpk, verdict, out_of_spec_pct)
               VALUES (?, '2024-01-01T00:00:00+00:00', ?, 200,
                       10.0, 0.1, 10.2, 9.8, 1.11, 1.11, 'warning', 0.5)""",
            (uid, proc),
        )
    conn.commit()
    rows = get_latest_cpk(conn)
    assert len(rows) == 3
    assert {r["process"] for r in rows} == {"溶接", "塗装", "組立"}


def test_get_latest_cpk_empty_when_no_data(conn):
    assert get_latest_cpk(conn) == []

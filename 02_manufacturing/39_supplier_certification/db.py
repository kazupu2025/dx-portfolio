"""サプライヤー品質認定 データベース CRUD。"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd

DB_PATH = Path(__file__).parent / "supplier_cert.db"


def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                contact TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
                period TEXT NOT NULL,
                quality_score REAL NOT NULL,
                delivery_score REAL NOT NULL,
                cost_score REAL NOT NULL,
                total_score REAL NOT NULL,
                certification TEXT NOT NULL,
                memo TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );
        """)
        conn.commit()


def _calc_total(q, d, c):
    """total_score = quality*0.5 + delivery*0.3 + cost*0.2"""
    return round(q * 0.5 + d * 0.3 + c * 0.2, 1)


def _certification(total):
    """認定区分を決定。"""
    if total >= 80:
        return "認定"
    elif total >= 60:
        return "条件付認定"
    return "保留"


def seed_sample_data():
    """サンプルデータを挿入（既に存在する場合はスキップ）。"""
    with get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0]
        if count > 0:
            return

        now = datetime.now().isoformat()

        # サプライヤーマスタ
        suppliers_data = [
            ("部品工業 A社", "部品"),
            ("材料商事 B社", "材料"),
            ("精密加工 C社", "加工"),
            ("サービス D社", "サービス"),
        ]
        for name, cat in suppliers_data:
            conn.execute(
                "INSERT INTO suppliers (name, category, contact, created_at) VALUES (?,?,?,?)",
                (name, cat, "", now),
            )
        conn.commit()

        # サプライヤーIDを取得
        supplier_ids = {
            row[0]: row[1]
            for row in conn.execute("SELECT name, id FROM suppliers").fetchall()
        }

        # 評価レコード
        assessments = [
            ("部品工業 A社", "2024-06", 88, 85, 80),
            ("部品工業 A社", "2024-03", 82, 80, 78),
            ("材料商事 B社", "2024-06", 72, 68, 65),
            ("精密加工 C社", "2024-06", 92, 90, 85),
            ("サービス D社", "2024-06", 55, 60, 58),
        ]
        for name, period, q, d, c in assessments:
            total = _calc_total(q, d, c)
            cert = _certification(total)
            conn.execute(
                """
                INSERT INTO assessments (supplier_id, period, quality_score, delivery_score, cost_score, total_score, certification, memo, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)
            """,
                (supplier_ids[name], period, q, d, c, total, cert, "", now),
            )
        conn.commit()


def get_latest_assessments() -> pd.DataFrame:
    """サプライヤーごとの最新評価を取得。"""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT s.id, s.name, s.category, a.period, a.quality_score, a.delivery_score,
                   a.cost_score, a.total_score, a.certification
            FROM suppliers s
            LEFT JOIN assessments a ON s.id = a.supplier_id
            WHERE a.id = (
                SELECT id FROM assessments WHERE supplier_id = s.id ORDER BY period DESC LIMIT 1
            ) OR a.id IS NULL
            ORDER BY a.total_score DESC NULLS LAST
        """
        ).fetchall()

    if not rows:
        return pd.DataFrame(
            columns=[
                "id",
                "name",
                "category",
                "period",
                "quality_score",
                "delivery_score",
                "cost_score",
                "total_score",
                "certification",
            ]
        )
    return pd.DataFrame([dict(r) for r in rows])


def get_all_assessments() -> pd.DataFrame:
    """全評価レコードを取得。"""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT s.name, a.* FROM assessments a JOIN suppliers s ON a.supplier_id = s.id
            ORDER BY s.name, a.period
        """
        ).fetchall()
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(r) for r in rows])


def add_supplier(name, category, contact=""):
    """サプライヤーを追加。"""
    now = datetime.now().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO suppliers (name, category, contact, created_at) VALUES (?,?,?,?)",
            (name, category, contact, now),
        )
        conn.commit()


def add_assessment(supplier_id, period, quality_score, delivery_score, cost_score, memo=""):
    """評価レコードを追加。"""
    total = _calc_total(quality_score, delivery_score, cost_score)
    cert = _certification(total)
    now = datetime.now().isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO assessments (supplier_id, period, quality_score, delivery_score, cost_score, total_score, certification, memo, created_at)
            VALUES (?,?,?,?,?,?,?,?,?)
        """,
            (supplier_id, period, quality_score, delivery_score, cost_score, total, cert, memo, now),
        )
        conn.commit()
    return total, cert


def get_suppliers() -> pd.DataFrame:
    """サプライヤー一覧を取得。"""
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM suppliers ORDER BY name").fetchall()
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(r) for r in rows])

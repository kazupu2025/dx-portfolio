"""FMEA データベース CRUD。"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd

DB_PATH = Path(__file__).parent / "fmea.db"

def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fmea_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                process_name TEXT NOT NULL,
                failure_mode TEXT NOT NULL,
                effect TEXT NOT NULL,
                severity INTEGER NOT NULL,
                cause TEXT NOT NULL,
                occurrence INTEGER NOT NULL,
                detection INTEGER NOT NULL,
                rpn INTEGER NOT NULL,
                current_control TEXT DEFAULT '',
                action_required TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()

def seed_sample_data():
    """サンプルFMEAデータを投入（DBが空の場合のみ）。"""
    with get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM fmea_items").fetchone()[0]
        if count > 0:
            return
        now = datetime.now().isoformat()
        samples = [
            ("溶接工程", "溶接強度不足", "製品強度低下", 8, "溶接電流の変動", 4, 3, 8*4*3, "目視検査", "溶接電流モニタリング導入"),
            ("組立工程", "部品組み付け忘れ", "機能不全", 9, "作業手順不明確", 3, 5, 9*3*5, "チェックリスト", "ポカヨケ設備導入"),
            ("塗装工程", "塗膜剥離", "外観不良", 6, "前処理不足", 5, 4, 6*5*4, "外観検査", "前処理工程見直し"),
            ("プレス工程", "寸法外れ", "組み立て不可", 7, "金型摩耗", 3, 2, 7*3*2, "定期測定", "金型交換頻度見直し"),
            ("検査工程", "見逃し", "クレーム発生", 9, "検査基準曖昧", 4, 6, 9*4*6, "マニュアル", "検査基準書改訂"),
        ]
        conn.executemany("""
            INSERT INTO fmea_items
            (process_name, failure_mode, effect, severity, cause, occurrence, detection, rpn, current_control, action_required, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, [(s[0],s[1],s[2],s[3],s[4],s[5],s[6],s[7],s[8],s[9],now,now) for s in samples])
        conn.commit()

def get_all_items() -> pd.DataFrame:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM fmea_items ORDER BY rpn DESC").fetchall()
    if not rows:
        return pd.DataFrame(columns=["id","process_name","failure_mode","effect","severity","cause","occurrence","detection","rpn","current_control","action_required","created_at","updated_at"])
    return pd.DataFrame([dict(r) for r in rows])

def add_item(process_name, failure_mode, effect, severity, cause, occurrence, detection, current_control, action_required) -> int:
    rpn = severity * occurrence * detection
    now = datetime.now().isoformat()
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO fmea_items (process_name, failure_mode, effect, severity, cause, occurrence, detection, rpn, current_control, action_required, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (process_name, failure_mode, effect, severity, cause, occurrence, detection, rpn, current_control, action_required, now, now))
        conn.commit()
        return cur.lastrowid

def update_item(item_id, severity, occurrence, detection, current_control, action_required):
    rpn = severity * occurrence * detection
    now = datetime.now().isoformat()
    with get_conn() as conn:
        conn.execute("""
            UPDATE fmea_items SET severity=?, occurrence=?, detection=?, rpn=?, current_control=?, action_required=?, updated_at=?
            WHERE id=?
        """, (severity, occurrence, detection, rpn, current_control, action_required, now, item_id))
        conn.commit()

def delete_item(item_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM fmea_items WHERE id=?", (item_id,))
        conn.commit()

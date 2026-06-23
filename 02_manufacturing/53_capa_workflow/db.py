import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "capa_workflow.db"

STATUSES = ["起票", "調査中", "対策立案", "効果確認", "完了"]

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS capa_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                assignee TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT '起票',
                priority TEXT NOT NULL DEFAULT '中',
                description TEXT,
                root_cause TEXT,
                action_plan TEXT,
                effect_result TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                due_date TEXT
            )
        """)
        conn.commit()

def seed_db():
    import datetime
    init_db()
    with get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM capa_items").fetchone()[0]
        if count == 0:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            samples = [
                ("溶接工程不良再発", "工程不良", "田中", "調査中", "高", "溶接部の気泡発生", "溶接条件の不安定", None, None, now, now, "2024-02-28"),
                ("外観検査見逃し", "検査精度", "鈴木", "対策立案", "中", "外観検査での見逃し多発", "照明不足と検査員疲労", "照明改善と休憩ルール変更", None, now, now, "2024-03-15"),
                ("材料受入不良", "受入検査", "山田", "完了", "低", "材料寸法外れ", "仕入先管理不足", "仕入先QC強化", "不良率0.5%→0.1%に改善", now, now, "2024-01-31"),
                ("設備定期点検漏れ", "設備管理", "佐藤", "起票", "高", "設備点検スケジュール未実施", None, None, None, now, now, "2024-04-30"),
                ("作業標準書未遵守", "教育訓練", "伊藤", "効果確認", "中", "新人作業者のミス増加", "OJT不足", "作業標準書改訂と教育実施", None, now, now, "2024-03-01"),
            ]
            conn.executemany("""
                INSERT INTO capa_items (title,category,assignee,status,priority,description,
                root_cause,action_plan,effect_result,created_at,updated_at,due_date)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, samples)
            conn.commit()

def get_all():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM capa_items ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]

def get_by_id(item_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM capa_items WHERE id=?", (item_id,)).fetchone()
        return dict(row) if row else None

def create_item(data: dict):
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO capa_items (title,category,assignee,status,priority,description,due_date,created_at,updated_at)
            VALUES (:title,:category,:assignee,:status,:priority,:description,:due_date,:now,:now)
        """, {**data, "now": now})
        conn.commit()

def advance_status(item_id: int):
    import datetime
    item = get_by_id(item_id)
    if item and item["status"] in STATUSES:
        idx = STATUSES.index(item["status"])
        if idx < len(STATUSES) - 1:
            new_status = STATUSES[idx + 1]
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with get_conn() as conn:
                conn.execute("UPDATE capa_items SET status=?, updated_at=? WHERE id=?", (new_status, now, item_id))
                conn.commit()
            return new_status
    return None

def update_field(item_id: int, field: str, value: str):
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    allowed = ["root_cause","action_plan","effect_result","description","assignee","priority","due_date"]
    if field not in allowed:
        return
    with get_conn() as conn:
        conn.execute(f"UPDATE capa_items SET {field}=?, updated_at=? WHERE id=?", (value, now, item_id))
        conn.commit()

def delete_item(item_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM capa_items WHERE id=?", (item_id,))
        conn.commit()

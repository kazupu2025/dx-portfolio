import pytest
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# テスト用一時DB
import db as db_module
DB_BACKUP = db_module.DB_PATH

def setup_module():
    db_module.DB_PATH = Path(__file__).parent / "test_capa.db"
    if db_module.DB_PATH.exists():
        try:
            db_module.DB_PATH.unlink()
        except PermissionError:
            pass
    db_module.init_db()

def teardown_module():
    db_module.DB_PATH = DB_BACKUP
    # Close any open connections
    try:
        test_db = Path(__file__).parent / "test_capa.db"
        if test_db.exists():
            test_db.unlink()
    except (PermissionError, FileNotFoundError):
        pass

import datetime
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def add_item(status="起票"):
    db_module.create_item({
        "title": "テストCAPA", "category": "テスト", "assignee": "担当者",
        "status": status, "priority": "中", "description": "テスト", "due_date": "2099-12-31"
    })

def test_empty_returns_dict():
    from analyze import analyze
    r = analyze()
    assert isinstance(r, dict)

def test_required_keys():
    from analyze import analyze
    r = analyze()
    for k in ["total","completed","completion_rate","status_df","overdue_count","verdict"]:
        assert k in r

def test_create_and_count():
    add_item("起票")
    from analyze import analyze
    r = analyze()
    assert r["total"] >= 1

def test_advance_status():
    add_item("起票")
    items = db_module.get_all()
    item_id = items[0]["id"]
    new_status = db_module.advance_status(item_id)
    assert new_status == "調査中"

def test_completion_rate_calculation():
    # Clear and reinitialize
    with db_module.get_conn() as conn:
        conn.execute("DELETE FROM capa_items")
        conn.commit()
    add_item("完了")
    add_item("完了")
    add_item("起票")
    from analyze import analyze
    r = analyze()
    assert abs(r["completion_rate"] - 66.67) < 1.0

def test_verdict_good():
    # Clear and reinitialize
    with db_module.get_conn() as conn:
        conn.execute("DELETE FROM capa_items")
        conn.commit()
    for _ in range(8): add_item("完了")
    for _ in range(2): add_item("起票")
    from analyze import analyze
    assert analyze()["verdict"] == "good"

def test_delete_item():
    items = db_module.get_all()
    db_module.delete_item(items[0]["id"])
    assert db_module.get_by_id(items[0]["id"]) is None

def test_update_field():
    add_item("調査中")
    items = db_module.get_all()
    db_module.update_field(items[0]["id"], "root_cause", "テスト原因")
    updated = db_module.get_by_id(items[0]["id"])
    assert updated["root_cause"] == "テスト原因"

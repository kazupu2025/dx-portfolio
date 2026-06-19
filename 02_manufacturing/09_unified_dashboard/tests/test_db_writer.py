"""_common/db_writer.py のテスト"""
import sqlite3
import pytest
from pathlib import Path
import sys

# dx-portfolio ルートを sys.path に追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from _common import db_writer


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    """各テストが独立した一時 DB を使う"""
    db_path = tmp_path / "test_quality.db"
    monkeypatch.setattr(db_writer, "DB_PATH", db_path)
    db_writer.init_db()
    return db_path


def test_init_db_creates_tables(tmp_db):
    conn = sqlite3.connect(tmp_db)
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    conn.close()
    assert {"uploads", "monthly_kpis", "cpk_results"} <= tables


def test_write_upload_returns_positive_int(tmp_db):
    uid = db_writer.write_upload("defect_rate", "jan.csv", 200)
    assert isinstance(uid, int) and uid > 0


def test_write_kpi_stored_correctly(tmp_db):
    uid = db_writer.write_upload("defect_rate", "jan.csv", 200)
    db_writer.write_kpi(uid, "defect_rate", "2024-01", "defect_rate", 0.012, "good")
    conn = sqlite3.connect(tmp_db)
    row = conn.execute(
        "SELECT value, verdict, category FROM monthly_kpis WHERE upload_id=?", (uid,)
    ).fetchone()
    conn.close()
    assert row[0] == pytest.approx(0.012)
    assert row[1] == "good"
    assert row[2] is None  # category 省略 → NULL


def test_write_cpk_results_multiple(tmp_db):
    uid = db_writer.write_upload("cpk", "meas.csv", 600)
    results = [
        {"process": "溶接", "n": 200, "mean": 10.02, "std": 0.087,
         "usl": 10.2, "lsl": 9.8, "cp": 1.45, "cpk": 1.38,
         "verdict": "良好", "out_of_spec_pct": 0.1},
        {"process": "塗装", "n": 200, "mean": 9.88, "std": 0.12,
         "usl": 10.2, "lsl": 9.8, "cp": 1.11, "cpk": 0.97,
         "verdict": "不可", "out_of_spec_pct": 2.3},
    ]
    db_writer.write_cpk_results(uid, results)
    conn = sqlite3.connect(tmp_db)
    count = conn.execute(
        "SELECT COUNT(*) FROM cpk_results WHERE upload_id=?", (uid,)
    ).fetchone()[0]
    conn.close()
    assert count == 2


def test_write_kpi_invalid_verdict_raises(tmp_db):
    uid = db_writer.write_upload("defect_rate", "jan.csv", 200)
    with pytest.raises(ValueError, match="verdict"):
        db_writer.write_kpi(uid, "defect_rate", "2024-01", "defect_rate", 0.012, "invalid_verdict")


def test_idempotent_init_db(tmp_db):
    # 複数回呼んでも例外が出ないこと
    db_writer.init_db()
    db_writer.init_db()


def test_db_path_created_if_not_exists(tmp_path, monkeypatch):
    db_path = tmp_path / "subdir" / "quality.db"
    monkeypatch.setattr(db_writer, "DB_PATH", db_path)
    db_writer.init_db()
    assert db_path.exists()


def test_cpk_verdict_mapping(tmp_db):
    """C-62 の verdict（日本語）が good/warning/alert に変換されること"""
    uid = db_writer.write_upload("cpk", "meas.csv", 600)
    results = [
        {"process": "A", "n": 200, "mean": 10.0, "std": 0.05,
         "usl": 10.2, "lsl": 9.8, "cp": 2.0, "cpk": 1.67,
         "verdict": "非常に良好", "out_of_spec_pct": 0.0},
        {"process": "B", "n": 200, "mean": 10.0, "std": 0.1,
         "usl": 10.2, "lsl": 9.8, "cp": 1.11, "cpk": 1.11,
         "verdict": "要改善", "out_of_spec_pct": 0.5},
        {"process": "C", "n": 200, "mean": 10.0, "std": 0.15,
         "usl": 10.2, "lsl": 9.8, "cp": 0.89, "cpk": 0.89,
         "verdict": "不可", "out_of_spec_pct": 2.5},
    ]
    db_writer.write_cpk_results(uid, results)
    conn = sqlite3.connect(tmp_db)
    verdicts = {r[0]: r[1] for r in conn.execute(
        "SELECT process, verdict FROM cpk_results WHERE upload_id=?", (uid,)
    ).fetchall()}
    conn.close()
    assert verdicts["A"] == "good"     # cpk=1.67 ≥ 1.33
    assert verdicts["B"] == "warning"  # cpk=1.11 ≥ 1.00
    assert verdicts["C"] == "alert"    # cpk=0.89 < 1.00

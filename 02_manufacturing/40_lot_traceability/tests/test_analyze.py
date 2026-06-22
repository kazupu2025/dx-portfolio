"""C-94 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze


def _make_df(rows):
    """Helper: list of tuples → DataFrame"""
    return pd.DataFrame(rows, columns=["from_node", "to_node", "edge_type", "lot_id", "quantity"])


_SAMPLE = [
    ("原材料A", "工程1", "材料→工程", "L001", 100),
    ("工程1", "工程2", "工程→工程", "L001", 95),
    ("工程2", "得意先X", "工程→出荷", "L001", 90),
]


def test_verdict_good():
    """ノード数 ≤ 10 → good"""
    df = _make_df(_SAMPLE)
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"


def test_verdict_warning():
    """ノード数 11〜20 → warning（12ノード版）"""
    rows = [
        ("鋼材A", "切削", "材料→工程", "L001", 100),
        ("鋼材B", "切削", "材料→工程", "L002", 80),
        ("鋼材C", "組立", "材料→工程", "L003", 60),
        ("樹脂D", "組立", "材料→工程", "L004", 40),
        ("金具E", "溶接", "材料→工程", "L005", 20),
        ("切削", "組立", "工程→工程", "L001", 95),
        ("組立", "溶接", "工程→工程", "L002", 75),
        ("溶接", "検査", "工程→工程", "L003", 55),
        ("検査", "得意先X", "工程→出荷", "L001", 90),
        ("検査", "得意先Y", "工程→出荷", "L002", 70),
        ("検査", "得意先Z", "工程→出荷", "L003", 50),
    ]
    df = _make_df(rows)
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"


def test_verdict_alert():
    """ノード数 > 20 → alert"""
    rows = []
    for i in range(25):
        rows.append((f"原材料{i}", f"工程{i}", "材料→工程", f"L{i:03}", 10))
    df = _make_df(rows)
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"


def test_n_nodes():
    """4ノード（原材料A, 工程1, 工程2, 得意先X）"""
    df = _make_df(_SAMPLE)
    result = analyze.run_analysis(df)
    assert result["n_nodes"] == 4


def test_n_edges():
    """3エッジ"""
    df = _make_df(_SAMPLE)
    result = analyze.run_analysis(df)
    assert result["n_edges"] == 3


def test_n_lots():
    """2ロット（L001, L002）"""
    rows = _SAMPLE + [("原材料A", "工程1", "材料→工程", "L002", 50)]
    df = _make_df(rows)
    result = analyze.run_analysis(df)
    assert result["n_lots"] == 2


def test_material_nodes():
    """edge_type='材料→工程' のノードが抽出される"""
    df = _make_df(_SAMPLE)
    result = analyze.run_analysis(df)
    assert "原材料A" in result["material_nodes"]


def test_missing_column_raises():
    """必須列が不足すると ValueError"""
    df = pd.DataFrame({"from_node": ["A"], "to_node": ["B"]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)

"""C-83 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze


def _make_df(change_ids, change_names, groups, values):
    return pd.DataFrame({
        "change_id":   change_ids,
        "change_name": change_names,
        "group":       groups,
        "value":       values,
    })


def _sig_before():
    """有意差あり用: 平均10 vs 平均7 で明確に異なる20サンプル。"""
    rng = np.random.default_rng(0)
    before = rng.normal(10.0, 0.5, 10).tolist()
    after  = rng.normal(7.0,  0.5, 10).tolist()
    return before, after


def _nosig_before():
    """有意差なし用: 同一分布20サンプル。"""
    rng = np.random.default_rng(1)
    before = rng.normal(5.0, 0.5, 10).tolist()
    after  = rng.normal(5.0, 0.5, 10).tolist()
    return before, after


def test_verdict_good():
    """significant_ratio = 100% → good"""
    b, a = _sig_before()
    rows = (
        [{"change_id":"CH001","change_name":"テスト変更","group":"変更前","value":v} for v in b] +
        [{"change_id":"CH001","change_name":"テスト変更","group":"変更後","value":v} for v in a]
    )
    result = analyze.run_analysis(pd.DataFrame(rows))
    assert result["verdict"] == "good"
    assert result["significant_ratio"] == pytest.approx(100.0)


def test_verdict_warning():
    """significant_ratio = 50% → warning (lower boundary)"""
    b1, a1 = _sig_before()
    b2, a2 = _nosig_before()
    rows = (
        [{"change_id":"CH001","change_name":"変更A","group":"変更前","value":v} for v in b1] +
        [{"change_id":"CH001","change_name":"変更A","group":"変更後","value":v} for v in a1] +
        [{"change_id":"CH002","change_name":"変更B","group":"変更前","value":v} for v in b2] +
        [{"change_id":"CH002","change_name":"変更B","group":"変更後","value":v} for v in a2]
    )
    result = analyze.run_analysis(pd.DataFrame(rows))
    assert result["verdict"] == "warning"
    assert result["significant_ratio"] == pytest.approx(50.0)


def test_verdict_alert():
    """significant_ratio = 0% → alert"""
    b, a = _nosig_before()
    rows = (
        [{"change_id":"CH001","change_name":"テスト変更","group":"変更前","value":v} for v in b] +
        [{"change_id":"CH001","change_name":"テスト変更","group":"変更後","value":v} for v in a]
    )
    result = analyze.run_analysis(pd.DataFrame(rows))
    assert result["verdict"] == "alert"
    assert result["significant_ratio"] == pytest.approx(0.0)


def test_verdict_good_lower_boundary():
    """significant_ratio = 80% → good (boundary)"""
    b1, a1 = _sig_before()
    b2, a2 = _sig_before()
    b3, a3 = _sig_before()
    b4, a4 = _sig_before()
    b5, a5 = _nosig_before()
    all_rows = []
    for cid, cname, b, a in [
        ("CH001","A",b1,a1), ("CH002","B",b2,a2),
        ("CH003","C",b3,a3), ("CH004","D",b4,a4),
        ("CH005","E",b5,a5)
    ]:
        all_rows += [{"change_id":cid,"change_name":cname,"group":"変更前","value":v} for v in b]
        all_rows += [{"change_id":cid,"change_name":cname,"group":"変更後","value":v} for v in a]
    result = analyze.run_analysis(pd.DataFrame(all_rows))
    assert result["verdict"] == "good"
    assert result["significant_ratio"] == pytest.approx(80.0)


def test_total_changes():
    b1, a1 = _sig_before()
    b2, a2 = _nosig_before()
    rows = (
        [{"change_id":"CH001","change_name":"変更A","group":"変更前","value":v} for v in b1] +
        [{"change_id":"CH001","change_name":"変更A","group":"変更後","value":v} for v in a1] +
        [{"change_id":"CH002","change_name":"変更B","group":"変更前","value":v} for v in b2] +
        [{"change_id":"CH002","change_name":"変更B","group":"変更後","value":v} for v in a2]
    )
    result = analyze.run_analysis(pd.DataFrame(rows))
    assert result["total_changes"] == 2


def test_significant_count():
    b1, a1 = _sig_before()
    b2, a2 = _nosig_before()
    rows = (
        [{"change_id":"CH001","change_name":"変更A","group":"変更前","value":v} for v in b1] +
        [{"change_id":"CH001","change_name":"変更A","group":"変更後","value":v} for v in a1] +
        [{"change_id":"CH002","change_name":"変更B","group":"変更前","value":v} for v in b2] +
        [{"change_id":"CH002","change_name":"変更B","group":"変更後","value":v} for v in a2]
    )
    result = analyze.run_analysis(pd.DataFrame(rows))
    assert result["significant_count"] == 1


def test_result_summary_columns():
    b, a = _sig_before()
    rows = (
        [{"change_id":"CH001","change_name":"テスト変更","group":"変更前","value":v} for v in b] +
        [{"change_id":"CH001","change_name":"テスト変更","group":"変更後","value":v} for v in a]
    )
    result = analyze.run_analysis(pd.DataFrame(rows))
    expected_cols = {"change_id","change_name","n_before","n_after","mean_before","mean_after",
                     "improvement_rate","p_value_t","p_value_mw","significant"}
    assert expected_cols.issubset(set(result["result_summary"].columns))


def test_missing_column_raises():
    df = pd.DataFrame({"change_id":["CH001"],"group":["変更前"]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)

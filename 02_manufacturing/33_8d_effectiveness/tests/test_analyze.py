"""C-87 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze


def _make_df(action_ids, action_names, groups, values):
    return pd.DataFrame({
        "action_id":   action_ids,
        "action_name": action_names,
        "group":       groups,
        "value":       values,
    })


def _two_actions_df(
    before1, after1,
    before2, after2,
):
    """2処置のデータフレームを生成するヘルパー。"""
    rows = []
    for v in before1:
        rows.append({"action_id": "A1", "action_name": "処置1", "group": "処置前", "value": v})
    for v in after1:
        rows.append({"action_id": "A1", "action_name": "処置1", "group": "処置後", "value": v})
    for v in before2:
        rows.append({"action_id": "A2", "action_name": "処置2", "group": "処置前", "value": v})
    for v in after2:
        rows.append({"action_id": "A2", "action_name": "処置2", "group": "処置後", "value": v})
    return pd.DataFrame(rows)


def test_verdict_good():
    """100%有効（2/2）→ effective_ratio=100.0 → good"""
    # A1: 有意差あり + 改善, A2: 有意差あり + 改善
    before = [10.0] * 10
    after  = [5.0]  * 10
    df = _two_actions_df(before, after, before, after)
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["effective_ratio"] >= 80.0


def test_verdict_warning():
    """50%有効（1/2）→ effective_ratio=50.0 → warning（下限境界）"""
    # A1: 有意差あり + 改善, A2: 差なし
    before_good = [10.0] * 10
    after_good  = [5.0]  * 10
    before_bad  = [5.0]  * 10
    after_bad   = [5.1]  * 10
    df = _two_actions_df(before_good, after_good, before_bad, after_bad)
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert result["effective_ratio"] == pytest.approx(50.0)


def test_verdict_alert():
    """0%有効（0/2）→ effective_ratio=0.0 → alert"""
    before = [5.0] * 10
    after  = [5.1] * 10
    df = _two_actions_df(before, after, before, after)
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["effective_ratio"] == pytest.approx(0.0)


def test_verdict_good_boundary():
    """80%有効（4/5）→ effective_ratio=80.0 → good（境界値）"""
    rows = []
    # 4処置: 有意差あり + 改善
    for i in range(1, 5):
        for v in [10.0] * 10:
            rows.append({"action_id": f"A{i}", "action_name": f"処置{i}", "group": "処置前", "value": v})
        for v in [5.0] * 10:
            rows.append({"action_id": f"A{i}", "action_name": f"処置{i}", "group": "処置後", "value": v})
    # 1処置: 差なし
    for v in [5.0] * 10:
        rows.append({"action_id": "A5", "action_name": "処置5", "group": "処置前", "value": v})
    for v in [5.1] * 10:
        rows.append({"action_id": "A5", "action_name": "処置5", "group": "処置後", "value": v})
    df = pd.DataFrame(rows)
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["effective_ratio"] == pytest.approx(80.0)


def test_total_actions():
    """total_actions の確認"""
    before = [10.0] * 10
    after  = [5.0]  * 10
    df = _two_actions_df(before, after, before, after)
    result = analyze.run_analysis(df)
    assert result["total_actions"] == 2


def test_effective_count():
    """effective_count の確認（1処置有効）"""
    before_good = [10.0] * 10
    after_good  = [5.0]  * 10
    before_bad  = [5.0]  * 10
    after_bad   = [5.1]  * 10
    df = _two_actions_df(before_good, after_good, before_bad, after_bad)
    result = analyze.run_analysis(df)
    assert result["effective_count"] == 1


def test_result_summary_columns():
    """result_summary に effective 列を含む必須列が存在する"""
    before = [10.0] * 10
    after  = [5.0]  * 10
    df = _two_actions_df(before, after, before, after)
    result = analyze.run_analysis(df)
    required = {
        "action_id", "action_name", "n_before", "n_after",
        "mean_before", "mean_after", "improvement_rate",
        "cohen_d", "p_value", "significant", "effective",
    }
    assert required.issubset(set(result["result_summary"].columns))


def test_missing_column_raises():
    """必須列不足で ValueError が発生する"""
    df = pd.DataFrame({"action_id": ["A1"], "group": ["処置前"]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)

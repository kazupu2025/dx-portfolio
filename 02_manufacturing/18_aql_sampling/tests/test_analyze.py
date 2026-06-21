"""C-72 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze  # noqa: E402


def test_lot_size_to_code():
    plan = analyze.get_sampling_plan(500, 1.0, 2)
    assert plan["code"] == "H"


def test_get_sampling_plan():
    result = analyze.get_sampling_plan(500, 1.0, 2)
    assert result["n"]  == 50
    assert result["ac"] == 1
    assert result["re"] == 2


def test_oc_curve_at_zero():
    pa = analyze.oc_curve(50, 1, [0.0])
    assert pa[0] == pytest.approx(1.0)


def test_oc_curve_at_one():
    # p=1.0, Ac=0 → Pa = 0.0（不良率100%でAc=0なら必ず不合格）
    pa = analyze.oc_curve(50, 0, [1.0])
    assert pa[0] == pytest.approx(0.0)


def test_judge_accept():
    result = analyze.judge_lot(1, 2)
    assert result["result"]  == "accept"
    assert result["verdict"] == "good"


def test_judge_reject():
    result = analyze.judge_lot(3, 2)
    assert result["result"]  == "reject"
    assert result["verdict"] == "alert"


def test_run_plan_keys():
    result = analyze.run_plan(500, 1.0, 2)
    expected = {"code", "n", "ac", "re", "oc_p", "oc_pa", "alpha", "rql", "beta"}
    assert set(result.keys()) == expected


def test_invalid_lot_size():
    with pytest.raises(ValueError):
        analyze.get_sampling_plan(1, 1.0, 2)

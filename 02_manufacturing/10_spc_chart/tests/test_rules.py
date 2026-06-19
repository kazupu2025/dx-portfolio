"""rules.detect_violations の 8ルール個別ユニットテスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import rules


def test_rule1_detects_3sigma():
    """1点が 3σ 外に出たとき Rule 1 に記録されること。"""
    xbars = [0.0] * 10
    xbars[4] = 3.5  # |3.5 - 0| > 3σ(=3)
    v = rules.detect_violations(xbars, cl=0.0, sigma=1.0)
    assert 4 in v[1]


def test_rule1_no_false_positive():
    """3σ 以内の点は Rule 1 に記録されないこと。"""
    xbars = [2.9] * 10  # |2.9| < 3
    v = rules.detect_violations(xbars, cl=0.0, sigma=1.0)
    assert v[1] == []


def test_rule2_detects_2of3():
    """連続3点中2点が同側2σ外→ Rule 2 でトリガー。"""
    xbars = [0.0] * 10
    xbars[0] = 2.1   # 2σ 超（正側）
    xbars[1] = 0.5   # 2σ 内
    xbars[2] = 2.2   # 2σ 超（正側）→ [0,1,2] で 2/3 が正側2σ外
    v = rules.detect_violations(xbars, cl=0.0, sigma=1.0)
    assert 2 in v[2]


def test_rule3_detects_4of5():
    """連続5点中4点が同側1σ外→ Rule 3 でトリガー。"""
    xbars = [0.0] * 10
    for i in [0, 1, 3, 4]:
        xbars[i] = 1.2  # 1σ 超（正側）
    xbars[2] = 0.5      # 1σ 内（5点中の例外1点）
    v = rules.detect_violations(xbars, cl=0.0, sigma=1.0)
    assert 4 in v[3]


def test_rule4_detects_8_same_side():
    """連続8点が全て中心線の同側→ Rule 4 でトリガー（index 7 が8点目）。"""
    xbars = [0.5] * 10  # 全点が CL（0.0）より上
    v = rules.detect_violations(xbars, cl=0.0, sigma=1.0)
    assert 7 in v[4]


def test_rule5_detects_trend():
    """連続6点が単調増加→ Rule 5 でトリガー（index 5 が6点目）。"""
    xbars = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0] + [0.0] * 4
    v = rules.detect_violations(xbars, cl=0.0, sigma=1.0)
    assert 5 in v[5]


def test_rule6_detects_alternating():
    """連続14点が交互に上下→ Rule 6 でトリガー（index 13 が14点目）。"""
    xbars = [1.0 if i % 2 == 0 else -1.0 for i in range(14)]
    v = rules.detect_violations(xbars, cl=0.0, sigma=1.0)
    assert 13 in v[6]


def test_rule7_detects_hugging():
    """連続15点が全て±1σ内（ハガーリング）→ Rule 7 でトリガー。"""
    xbars = [0.5] * 15  # |0.5| < 1σ
    v = rules.detect_violations(xbars, cl=0.0, sigma=1.0)
    assert 14 in v[7]


def test_rule8_detects_mixture():
    """連続8点が全て±1σ外（両側混在）→ Rule 8 でトリガー（index 7）。"""
    xbars = [1.5, -1.5, 1.5, -1.5, 1.5, -1.5, 1.5, -1.5] + [0.0] * 2
    v = rules.detect_violations(xbars, cl=0.0, sigma=1.0)
    assert 7 in v[8]


def test_rule1_r_detects_ucl_exceedance():
    """R 管理図の UCL 超過点が検出されること。"""
    rs = [0.1, 0.2, 0.5, 0.1, 0.2]  # index 2 が UCL(=0.4) 超過
    result = rules.rule1_r(rs, r_ucl=0.4)
    assert result == [2]

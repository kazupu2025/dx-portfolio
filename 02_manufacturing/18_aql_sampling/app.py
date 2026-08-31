# -*- coding: utf-8 -*-
"""
B-85: 製造 AQL抜き取り検査・ロット合否判定ダッシュボード
JIS Z 9015-1 / ISO 2859-1 準拠のサンプリング計画 + OC曲線
スタンドアロン版（ローカルモジュール依存を排除）
"""
from __future__ import annotations
import math
import numpy as np
import streamlit as st
from pathlib import Path

try:
    import plotly.graph_objects as go
    _HAS_PLOTLY = True
except ImportError:
    _HAS_PLOTLY = False

BASE_DIR = Path(__file__).resolve().parent

# ── JIS Z 9015-1 テーブル（インライン） ──────────────────────────
VALID_AQL = [0.065, 0.10, 0.15, 0.25, 0.40, 0.65, 1.0, 1.5, 2.5, 4.0, 6.5, 10.0]

# ロットサイズ → コードレター（水準 I=0, II=1, III=2）
_LOT_CODE_TABLE = [
    (2,       8,      ["A", "A", "B"]),
    (9,       15,     ["A", "B", "C"]),
    (16,      25,     ["B", "C", "D"]),
    (26,      50,     ["C", "D", "E"]),
    (51,      90,     ["C", "E", "F"]),
    (91,      150,    ["D", "F", "G"]),
    (151,     280,    ["E", "G", "H"]),
    (281,     500,    ["F", "H", "J"]),
    (501,     1200,   ["G", "J", "K"]),
    (1201,    3200,   ["H", "K", "L"]),
    (3201,    10000,  ["J", "L", "M"]),
    (10001,   35000,  ["K", "M", "N"]),
    (35001,   150000, ["L", "N", "P"]),
    (150001,  500000, ["M", "P", "Q"]),
    (500001, 9999999, ["N", "Q", "R"]),
]

_CODE_SIZE = {
    "A": 2,  "B": 3,  "C": 5,  "D": 8,  "E": 13, "F": 20,
    "G": 32, "H": 50, "J": 80, "K": 125,"L": 200, "M": 315,
    "N": 500,"P": 800,"Q": 1250,"R": 2000,
}

# (コードレター, AQL%) → (Ac, Re)  ※ 普通検査 一回抜取
# ↑ = 一つ上のコードレターを使う（簡略のため最小コードで0/1を採用）
_PLAN_TABLE: dict[tuple, tuple] = {
    # AQL 0.065
    ("L", 0.065): (0, 1), ("M", 0.065): (1, 2), ("N", 0.065): (2, 3),
    ("P", 0.065): (3, 4), ("Q", 0.065): (5, 6),
    # AQL 0.10
    ("K", 0.10): (0, 1), ("L", 0.10): (1, 2), ("M", 0.10): (2, 3),
    ("N", 0.10): (3, 4), ("P", 0.10): (5, 6), ("Q", 0.10): (7, 8),
    # AQL 0.15
    ("J", 0.15): (0, 1), ("K", 0.15): (1, 2), ("L", 0.15): (2, 3),
    ("M", 0.15): (3, 4), ("N", 0.15): (5, 6), ("P", 0.15): (7, 8),
    # AQL 0.25
    ("H", 0.25): (0, 1), ("J", 0.25): (1, 2), ("K", 0.25): (2, 3),
    ("L", 0.25): (3, 4), ("M", 0.25): (5, 6), ("N", 0.25): (7, 8),
    # AQL 0.40
    ("G", 0.40): (0, 1), ("H", 0.40): (1, 2), ("J", 0.40): (2, 3),
    ("K", 0.40): (3, 4), ("L", 0.40): (5, 6), ("M", 0.40): (7, 8),
    ("N", 0.40): (10, 11),
    # AQL 0.65
    ("F", 0.65): (0, 1), ("G", 0.65): (1, 2), ("H", 0.65): (2, 3),
    ("J", 0.65): (3, 4), ("K", 0.65): (5, 6), ("L", 0.65): (7, 8),
    ("M", 0.65): (10, 11), ("N", 0.65): (14, 15),
    # AQL 1.0
    ("E", 1.0): (0, 1), ("F", 1.0): (1, 2), ("G", 1.0): (2, 3),
    ("H", 1.0): (3, 4), ("J", 1.0): (5, 6), ("K", 1.0): (7, 8),
    ("L", 1.0): (10, 11), ("M", 1.0): (14, 15), ("N", 1.0): (21, 22),
    # AQL 1.5
    ("D", 1.5): (0, 1), ("E", 1.5): (1, 2), ("F", 1.5): (2, 3),
    ("G", 1.5): (3, 4), ("H", 1.5): (5, 6), ("J", 1.5): (7, 8),
    ("K", 1.5): (10, 11), ("L", 1.5): (14, 15), ("M", 1.5): (21, 22),
    # AQL 2.5
    ("C", 2.5): (0, 1), ("D", 2.5): (1, 2), ("E", 2.5): (2, 3),
    ("F", 2.5): (3, 4), ("G", 2.5): (5, 6), ("H", 2.5): (7, 8),
    ("J", 2.5): (10, 11), ("K", 2.5): (14, 15), ("L", 2.5): (21, 22),
    # AQL 4.0
    ("B", 4.0): (0, 1), ("C", 4.0): (1, 2), ("D", 4.0): (2, 3),
    ("E", 4.0): (3, 4), ("F", 4.0): (5, 6), ("G", 4.0): (7, 8),
    ("H", 4.0): (10, 11), ("J", 4.0): (14, 15), ("K", 4.0): (21, 22),
    # AQL 6.5
    ("A", 6.5): (0, 1), ("B", 6.5): (1, 2), ("C", 6.5): (2, 3),
    ("D", 6.5): (3, 4), ("E", 6.5): (5, 6), ("F", 6.5): (7, 8),
    ("G", 6.5): (10, 11), ("H", 6.5): (14, 15), ("J", 6.5): (21, 22),
    # AQL 10.0
    ("A", 10.0): (1, 2), ("B", 10.0): (2, 3), ("C", 10.0): (3, 4),
    ("D", 10.0): (5, 6), ("E", 10.0): (7, 8), ("F", 10.0): (10, 11),
    ("G", 10.0): (14, 15), ("H", 10.0): (21, 22),
}

_CODE_ORDER = ["A","B","C","D","E","F","G","H","J","K","L","M","N","P","Q","R"]


def _get_code(lot_size: int, level: int) -> str:
    for lo, hi, codes in _LOT_CODE_TABLE:
        if lo <= lot_size <= hi:
            return codes[level]
    return "R"


def _binom_cdf(n: int, ac: int, p: float) -> float:
    """P(X <= ac) for X ~ Binomial(n, p)"""
    if p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 1.0 if ac >= n else 0.0
    prob = 0.0
    log_p    = math.log(p)
    log_1_p  = math.log(1.0 - p)
    log_binom = 0.0
    for k in range(min(ac + 1, n + 1)):
        if k > 0:
            log_binom += math.log(n - k + 1) - math.log(k)
        log_term = log_binom + k * log_p + (n - k) * log_1_p
        prob += math.exp(log_term)
    return min(1.0, prob)


def _run_b85_plan(lot_size: int, aql: float, level: int) -> dict:
    code = _get_code(lot_size, level)

    # AQL テーブルで見つからない場合は上のコードを試す
    key = (code, aql)
    if key not in _PLAN_TABLE:
        idx = _CODE_ORDER.index(code)
        found = False
        for i in range(idx, len(_CODE_ORDER)):
            if (_CODE_ORDER[i], aql) in _PLAN_TABLE:
                code = _CODE_ORDER[i]
                key  = (code, aql)
                found = True
                break
        if not found:
            raise ValueError(f"AQL={aql}% のサンプリング計画が見つかりません。ロットサイズを増やすか AQL を下げてください。")

    ac, re = _PLAN_TABLE[key]
    n = _CODE_SIZE[code]

    # n > lot_size の場合は全数検査
    if n >= lot_size:
        n = lot_size
        ac = 0
        re = 1

    # OC 曲線（p=0〜20% の範囲で計算）
    p_vals  = [i / 200 for i in range(0, 201)]   # 0〜100% を 0.5% 刻み
    pa_vals = [_binom_cdf(n, ac, p) for p in p_vals]

    # 生産者リスク α（AQL での不合格確率）
    alpha = 1.0 - _binom_cdf(n, ac, aql / 100.0)

    # 消費者リスク β（RQL = p で合格確率 ≤ 10% となる p を探す）
    rql = aql / 100.0
    for p in p_vals:
        if _binom_cdf(n, ac, p) <= 0.10:
            rql = p
            break
    beta = _binom_cdf(n, ac, rql)

    return {
        "code": code, "n": n, "ac": ac, "re": re,
        "oc_p": p_vals, "oc_pa": pa_vals,
        "alpha": alpha, "rql": rql, "beta": beta,
    }


def _judge_b85_lot(defects: int, ac: int) -> dict:
    if defects <= ac:
        return {"verdict": "good", "result": "accept"}
    return {"verdict": "alert", "result": "reject"}


# ── OC 曲線（インライン） ──────────────────────────────────────
def _b85_oc_chart(p_vals, pa_vals, aql, alpha, rql, beta):
    fig = go.Figure()
    fig.add_scatter(
        x=[v * 100 for v in p_vals], y=pa_vals,
        mode="lines", line=dict(color="#1e3a5f", width=2.5), name="合格確率 Pa(p)",
    )
    # AQL マーカー
    fig.add_scatter(
        x=[aql], y=[1.0 - alpha],
        mode="markers+text",
        marker=dict(color="#16a34a", size=10, symbol="circle"),
        text=[f"AQL={aql}%\nPa={1-alpha:.1%}"],
        textposition="top right", name=f"AQL={aql}%",
    )
    # RQL マーカー
    fig.add_scatter(
        x=[rql * 100], y=[beta],
        mode="markers+text",
        marker=dict(color="#dc2626", size=10, symbol="diamond"),
        text=[f"RQL={rql*100:.1f}%\nPa={beta:.1%}"],
        textposition="top right", name=f"RQL={rql*100:.1f}%",
    )
    fig.update_layout(
        title="OC 曲線（検査特性曲線）",
        xaxis_title="不良率 p (%)",
        yaxis_title="合格確率 Pa(p)",
        yaxis=dict(range=[0, 1.05]),
        xaxis=dict(range=[0, 20]),
        height=400,
        legend=dict(orientation="h", y=-0.2),
    )
    return fig


# ── UI ─────────────────────────────────────────────────────────
st.title("📋 B-85 AQL抜き取り検査・ロット合否判定")
st.caption("B-85 | 製造 × 品質管理 | JIS Z 9015-1 準拠のサンプリング計画 + OC曲線 + ロット判定")

for key in ["b85_plan", "b85_params", "b85_judgment"]:
    if key not in st.session_state:
        st.session_state[key] = None

with st.sidebar:
    st.header("⚙ 計画設計")
    lot_size = st.number_input(
        "ロットサイズ N", min_value=2, max_value=500000, value=500, step=1,
        key="b85_lot_size",
    )
    aql = st.selectbox(
        "AQL 水準（%）", options=VALID_AQL,
        index=VALID_AQL.index(1.0),
        format_func=lambda v: f"{v}%",
        key="b85_aql",
    )
    inspection_level = st.radio(
        "検査水準", options=[1, 2, 3], index=1,
        format_func=lambda v: f"水準 {'I' if v == 1 else 'II' if v == 2 else 'III'}",
        horizontal=True, key="b85_level",
    )
    run_btn = st.button("▶ 計画作成", type="primary", use_container_width=True,
                         key="b85_run")

    st.divider()
    st.header("🔍 ロット判定（任意）")
    st.caption("計画作成後に不良数を入力")
    defects = st.number_input("実際の不良数 d", min_value=0, value=0, step=1,
                               key="b85_defects")
    judge_btn = st.button("▶ 判定", use_container_width=True, key="b85_judge")

if run_btn:
    try:
        result = _run_b85_plan(int(lot_size), float(aql), inspection_level - 1)
        st.session_state.b85_plan   = result
        st.session_state.b85_params = {
            "lot_size": int(lot_size), "aql": float(aql),
            "inspection_level": inspection_level,
        }
        st.session_state.b85_judgment = None
    except ValueError as e:
        st.error(str(e))

plan = st.session_state.b85_plan
if plan is None:
    st.info("サイドバーの「▶ 計画作成」をクリックしてサンプリング計画を生成してください。")
    st.stop()

params = st.session_state.b85_params

# ── KPI 4列 ──────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("サンプルサイズコード", plan["code"])
c2.metric("抜取数", f"{plan['n']} 個")
c3.metric("合格判定数", f"Ac = {plan['ac']}")
c4.metric("不合格判定数", f"Re = {plan['re']}")

# ── OC 曲線 ──────────────────────────────────────────────────
if _HAS_PLOTLY:
    fig = _b85_oc_chart(
        plan["oc_p"], plan["oc_pa"],
        params["aql"], plan["alpha"], plan["rql"], plan["beta"],
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    oc_df = {"不良率(%)": [v * 100 for v in plan["oc_p"]],
             "合格確率 Pa": plan["oc_pa"]}
    import pandas as pd
    st.line_chart(pd.DataFrame(oc_df).set_index("不良率(%)"))

st.caption(
    f"生産者リスク α = {plan['alpha']:.1%}（AQL={params['aql']}% 時の不合格確率）　"
    f"消費者リスク β = {plan['beta']:.1%}（RQL={plan['rql']*100:.1f}% 時の合格確率）"
)

# ── ロット判定 ───────────────────────────────────────────────
if judge_btn:
    judgment = _judge_b85_lot(int(defects), plan["ac"])
    st.session_state.b85_judgment = {"judgment": judgment, "defects": int(defects)}

judgment_state = st.session_state.b85_judgment
if judgment_state:
    j = judgment_state["judgment"]
    d = judgment_state["defects"]
    _COLOR = {"good": "#16a34a", "alert": "#dc2626"}
    _LABEL = {"good": "✅ 合格", "alert": "❌ 不合格"}
    v = j["verdict"]
    st.markdown(
        f'<div style="background:{_COLOR[v]}22;border-left:4px solid {_COLOR[v]};'
        f'padding:12px 16px;border-radius:4px;margin-top:12px">'
        f'<b style="color:{_COLOR[v]};font-size:20px">'
        f'{_LABEL[v]}（不良数 {d} 個 / Ac={plan["ac"]}）</b>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── 計画サマリー テーブル ─────────────────────────────────────
st.subheader("サンプリング計画サマリー")
import pandas as pd
summary_df = pd.DataFrame([{
    "ロットサイズ N": params["lot_size"],
    "AQL (%)": params["aql"],
    "検査水準": f"水準 {'I' if params['inspection_level']==1 else 'II' if params['inspection_level']==2 else 'III'}",
    "コードレター": plan["code"],
    "抜取数 n": plan["n"],
    "合格判定数 Ac": plan["ac"],
    "不合格判定数 Re": plan["re"],
    "生産者リスク α": f"{plan['alpha']:.1%}",
    "RQL (%)": f"{plan['rql']*100:.1f}",
    "消費者リスク β": f"{plan['beta']:.1%}",
}])
st.dataframe(summary_df.T.rename(columns={0: "値"}), use_container_width=True)

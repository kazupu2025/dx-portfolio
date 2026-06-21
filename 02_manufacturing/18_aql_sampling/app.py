"""AQL/受入サンプリング計画最適化 — JIS Z 9015-1 × OC 曲線 × ロット合否判定。"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import analyze
import visualize
from tables import VALID_AQL

st.set_page_config(page_title="AQL 受入サンプリング計画", page_icon="📋", layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #f5f7fa; }
[data-testid="stHeader"] { background-color: #f5f7fa; }
.block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div style="background:#1e3a5f;color:white;padding:12px 20px;'
    'border-radius:6px;margin-bottom:16px">'
    '<h3 style="margin:0;font-family:BIZ UDGothic">'
    "📋 AQL/受入サンプリング計画最適化 — JIS Z 9015-1 × OC 曲線</h3>"
    "</div>",
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙ 計画設計")
    lot_size = st.number_input(
        "ロットサイズ N", min_value=2, max_value=500000, value=500, step=1,
    )
    aql = st.selectbox(
        "AQL 水準（%）",
        options=VALID_AQL,
        index=VALID_AQL.index(1.0),
        format_func=lambda v: f"{v}%",
    )
    inspection_level = st.radio(
        "検査水準",
        options=[1, 2, 3],
        index=1,
        format_func=lambda v: f"水準 {'I' if v == 1 else 'II' if v == 2 else 'III'}",
        horizontal=True,
    )
    run_btn = st.button("▶ 計画作成", type="primary", use_container_width=True)

    st.divider()
    st.header("🔍 ロット判定（任意）")
    st.caption("計画作成後に不良数を入力")
    defects = st.number_input("実際の不良数 d", min_value=0, value=0, step=1)
    judge_btn = st.button("▶ 判定 + 記録", use_container_width=True)

# ── 計画作成 ──────────────────────────────────────────────────────
if run_btn:
    try:
        result = analyze.run_plan(lot_size, aql, inspection_level)
        st.session_state["plan"]   = result
        st.session_state["params"] = {"lot_size": lot_size, "aql": aql,
                                      "inspection_level": inspection_level}
        st.session_state.pop("judgment", None)
    except ValueError as e:
        st.error(str(e))
        st.stop()

plan = st.session_state.get("plan")
if not plan:
    st.info("サイドバーの「▶ 計画作成」をクリックしてサンプリング計画を生成してください。")
    st.stop()

# ── KPI 4列 ───────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("サンプルサイズコード", plan["code"])
c2.metric("抜取数", f"{plan['n']} 個")
c3.metric("合格判定数", f"Ac = {plan['ac']}")
c4.metric("不合格判定数", f"Re = {plan['re']}")

# ── OC 曲線 ───────────────────────────────────────────────────────
params = st.session_state["params"]
fig = visualize.oc_chart(
    plan["oc_p"], plan["oc_pa"],
    params["aql"], plan["alpha"],
    plan["rql"],   plan["beta"],
)
st.plotly_chart(fig, use_container_width=True)

st.caption(
    f"生産者リスク α={plan['alpha']:.1%}（AQL={params['aql']}% 時の不合格確率）　"
    f"消費者リスク β={plan['beta']:.1%}（RQL={plan['rql']*100:.1f}% 時の合格確率）"
)

# ── ロット判定 ────────────────────────────────────────────────────
if judge_btn:
    judgment = analyze.judge_lot(int(defects), plan["ac"])
    st.session_state["judgment"] = judgment

    _COLOR = {"good": "#16a34a", "alert": "#dc2626"}
    _LABEL = {"good": "合格", "alert": "不合格"}
    v = judgment["verdict"]
    st.markdown(
        f'<div style="background:{_COLOR[v]}22;border-left:4px solid {_COLOR[v]};'
        f'padding:12px 16px;border-radius:4px;margin-top:12px">'
        f'<b style="color:{_COLOR[v]};font-size:20px">'
        f'{_LABEL[v]}（不良数 {defects} 個 / Ac={plan["ac"]}）</b>'
        f'</div>',
        unsafe_allow_html=True,
    )

    try:
        from _common.db_writer import init_db, write_upload, write_kpi
        init_db()
        uid = write_upload(
            "aql_sampling",
            f"lot_N{params['lot_size']}_AQL{params['aql']}",
            1,
        )
        write_kpi(
            uid, "aql_sampling",
            datetime.now().strftime("%Y-%m"),
            "acceptance",
            1.0 if judgment["result"] == "accept" else 0.0,
            judgment["verdict"],
        )
    except Exception as _e:
        st.caption(f"⚠ DB書き込みスキップ: {_e}")

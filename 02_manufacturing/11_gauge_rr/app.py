"""ゲージR&R（MSA）アプリ — 2要因 ANOVA による測定システム分析。"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import analyze
import visualize
from sample_data import generate_sample_csv

st.set_page_config(page_title="ゲージR&R（MSA）", page_icon="🔬", layout="wide")

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
    '🔬 ゲージR&R（MSA）— 2要因 ANOVA 測定システム分析</h3>'
    "</div>",
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙ 設定")
    use_sample = st.button("サンプルデータを使用", use_container_width=True)
    uploaded   = st.file_uploader("CSVアップロード", type=["csv"])

    if use_sample:
        st.session_state["df"] = generate_sample_csv()
    elif uploaded:
        st.session_state["df"] = pd.read_csv(uploaded)

    df: pd.DataFrame | None = st.session_state.get("df")

    part_col = op_col = value_col = None
    run_btn = False

    if df is not None:
        cols      = df.columns.tolist()
        part_col  = st.selectbox("部品列",   cols, key="part_col")
        op_col    = st.selectbox("作業者列", cols, index=min(1, len(cols) - 1), key="op_col")
        value_col = st.selectbox("測定値列", cols, index=min(3, len(cols) - 1), key="value_col")
        run_btn   = st.button("▶ 分析実行", type="primary", use_container_width=True)

# ── Main area ──────────────────────────────────────────────────────
if df is None:
    st.info("サイドバーから CSV をアップロードするか、「サンプルデータを使用」をクリックしてください。")
    st.stop()

if run_btn:
    if not all([part_col, op_col, value_col]):
        st.error("列をすべて選択してください。")
        st.stop()
    try:
        result = analyze.run_analysis(df, value_col, part_col, op_col)
        st.session_state.update({
            "result":   result,
            "part_col": part_col, "op_col": op_col, "value_col": value_col,
            "uploaded_name": uploaded.name if uploaded else "sample_gauge_rr.csv",
            "row_count": len(df),
        })
    except ValueError as e:
        st.error(str(e))
        st.stop()

result    = st.session_state.get("result")
part_col  = st.session_state.get("part_col",  part_col)
op_col    = st.session_state.get("op_col",    op_col)
value_col = st.session_state.get("value_col", value_col)

if not result:
    st.info("サイドバーで設定を選択し、「▶ 分析実行」を押してください。")
    st.stop()

# KPI サマリー
pct     = result["grr_pct"]
v_color = "#16a34a" if pct < 10 else "#d97706" if pct < 30 else "#dc2626"
v_label = "合格" if pct < 10 else "条件付き合格" if pct < 30 else "不合格"

c1, c2, c3, c4 = st.columns(4)
c1.metric("%GRR",             f"{result['grr_pct']:.1f}%")
c2.metric("%EV（繰り返し性）", f"{result['ev_pct']:.1f}%")
c3.metric("%AV（再現性）",     f"{result['av_pct']:.1f}%")
c4.markdown(
    f'<div style="background:{v_color}22;border-left:4px solid {v_color};'
    f'padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{v_color};font-size:16px">{v_label}</b><br>'
    f'<span style="font-size:12px;color:#64748b">ndc = {result["ndc"]}</span></div>',
    unsafe_allow_html=True,
)

# チャート
st.plotly_chart(visualize.cov_chart(result), use_container_width=True)

col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(
        visualize.scatter_chart(df, part_col, op_col, value_col),
        use_container_width=True,
    )
with col_r:
    st.plotly_chart(
        visualize.xbar_chart(df, part_col, op_col, value_col),
        use_container_width=True,
    )

# ANOVA テーブル
st.subheader("ANOVA テーブル")
st.dataframe(
    result["anova_table"].style.format(
        {"SS": "{:.4f}", "MS": "{:.4f}", "F": "{:.3f}", "p値": "{:.4f}"}, na_rep="—"
    ),
    hide_index=True, use_container_width=True,
)

# DB 書き込み（失敗してもアプリは継続）
try:
    from _common.db_writer import init_db, write_upload, write_kpi
    init_db()
    uid     = write_upload("msa", st.session_state.get("uploaded_name"), st.session_state.get("row_count"))
    verdict = "good" if pct < 10 else "warning" if pct < 30 else "alert"
    write_kpi(uid, "msa", datetime.now().strftime("%Y-%m"), "grr_pct", pct, verdict)
except Exception as _e:
    st.caption(f"⚠ DB書き込みスキップ: {_e}")

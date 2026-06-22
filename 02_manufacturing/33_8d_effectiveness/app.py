"""是正処置（8D）効果検証 — 統計的有意差検定。"""
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
import analyze, visualize
from sample_data import generate_sample_csv

st.set_page_config(page_title="8D効果検証", page_icon="🔬", layout="wide")
st.markdown("""<style>
[data-testid="stAppViewContainer"]{background-color:#f5f7fa;}
[data-testid="stHeader"]{background-color:#f5f7fa;}
.block-container{padding-top:1rem;}
</style>""", unsafe_allow_html=True)
st.markdown(
    '<div style="background:#1e3a5f;color:white;padding:12px 20px;border-radius:6px;margin-bottom:16px">'
    '<h3 style="margin:0;font-family:BIZ UDGothic">🔬 是正処置（8D）効果検証 — 統計的有意差検定</h3></div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙ 設定")
    st.caption("CSV 列: action_id / action_name / group（処置前・処置後）/ value")
    uploaded   = st.file_uploader("CSVアップロード", type=["csv"])
    use_sample = st.button("サンプルデータを使用", use_container_width=True)
    if uploaded:
        st.session_state["df"] = pd.read_csv(uploaded)
    elif use_sample:
        st.session_state["df"] = generate_sample_csv()
    df = st.session_state.get("df")
    run_btn = False
    if df is not None:
        run_btn = st.button("▶ 分析実行", type="primary", use_container_width=True)

if df is None:
    st.info("サイドバーから CSV をアップロードするか、「サンプルデータを使用」をクリックしてください。")
    st.stop()

if run_btn:
    try:
        result = analyze.run_analysis(df)
        st.session_state.update({
            "result": result,
            "uploaded_name": uploaded.name if uploaded else "sample_8d_effectiveness.csv",
            "row_count": len(df),
        })
    except ValueError as e:
        st.error(str(e))
        st.stop()
    try:
        from _common.db_writer import init_db, write_upload, write_kpi
        init_db()
        uid = write_upload("8d_effectiveness", st.session_state.get("uploaded_name"), st.session_state.get("row_count"))
        write_kpi(uid, "8d_effectiveness", datetime.now().strftime("%Y-%m"),
                  "effective_ratio",
                  float(st.session_state["result"]["effective_ratio"]),
                  st.session_state["result"]["verdict"])
    except Exception as _e:
        st.caption(f"⚠ DB書き込みスキップ: {_e}")

result = st.session_state.get("result")
if not result:
    st.info("「▶ 分析実行」を押してください。")
    st.stop()

er   = result["effective_ratio"]
ec   = result["effective_count"]
ta   = result["total_actions"]
ba   = result["best_action"]
vd   = result["verdict"]
_C   = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_L   = {"good": "効果的", "warning": "要改善", "alert": "再評価要"}
vc, vl = _C[vd], _L[vd]

c1, c2, c3, c4 = st.columns(4)
c1.metric("処置有効率", f"{er:.1f}%")
c2.metric("有効件数", f"{ec} / {ta} 件")
c3.metric("最大改善処置", ba or "—")
c4.markdown(
    f'<div style="background:{vc}22;border-left:4px solid {vc};padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{vc};font-size:16px">{vl}</b><br>'
    f'<span style="font-size:12px;color:#64748b">有効率 {er:.1f}%（{ec}/{ta}処置）</span></div>',
    unsafe_allow_html=True,
)

col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(visualize.effectiveness_bar_chart(result["result_summary"]), use_container_width=True)
with col_r:
    st.plotly_chart(visualize.effect_size_chart(result["result_summary"]), use_container_width=True)

st.subheader("処置別 統計検定結果")
display_df = result["result_summary"].copy()
display_df["有効"] = display_df["effective"].map({True: "✅ 有効", False: "❌ 無効"})
display_df["有意差"] = display_df["significant"].map({True: "◎", False: "—"})
display_df = display_df.drop(columns=["effective", "significant"])
st.dataframe(display_df, use_container_width=True)

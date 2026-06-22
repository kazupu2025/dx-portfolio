"""AQL/受入サンプリング計画最適化（OC曲線）。"""
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

st.set_page_config(page_title="AQLサンプリング計画最適化", page_icon="🔎", layout="wide")
st.markdown("""<style>
[data-testid="stAppViewContainer"]{background-color:#f5f7fa;}
[data-testid="stHeader"]{background-color:#f5f7fa;}
.block-container{padding-top:1rem;}
</style>""", unsafe_allow_html=True)
st.markdown(
    '<div style="background:#1e3a5f;color:white;padding:12px 20px;border-radius:6px;margin-bottom:16px">'
    '<h3 style="margin:0;font-family:BIZ UDGothic">🔎 AQL/受入サンプリング計画最適化（OC曲線）</h3></div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙ 設定")
    st.caption("CSV 列: lot_size / sample_size / acceptance_number / aql_pct")
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
            "uploaded_name": uploaded.name if uploaded else "sample_aql_sampling.csv",
            "row_count": len(df),
        })
    except ValueError as e:
        st.error(str(e))
        st.stop()
    try:
        from _common.db_writer import init_db, write_upload, write_kpi
        init_db()
        uid = write_upload("aql_sampling", st.session_state.get("uploaded_name"), st.session_state.get("row_count"))
        write_kpi(uid, "aql_sampling", datetime.now().strftime("%Y-%m"),
                  "avg_pa",
                  float(st.session_state["result"]["avg_pa_at_aql"]),
                  st.session_state["result"]["verdict"])
    except Exception as _e:
        st.caption(f"⚠ DB書き込みスキップ: {_e}")

result = st.session_state.get("result")
if not result:
    st.info("「▶ 分析実行」を押してください。")
    st.stop()

pa   = result["avg_pa_at_aql"]
aps  = result["avg_protection_score"]
bp   = result["best_plan"]
np_  = result["n_plans"]
vd   = result["verdict"]
_C   = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_L   = {"good": "計画適切", "warning": "要見直し", "alert": "計画不適"}
vc, vl = _C[vd], _L[vd]

c1, c2, c3, c4 = st.columns(4)
c1.metric("AQL合格確率", f"{pa:.3f}")
c2.metric("平均保護スコア", f"{aps:.3f}")
c3.metric("最優秀計画ロットサイズ", f"{bp:,}")
c4.markdown(
    f'<div style="background:{vc}22;border-left:4px solid {vc};padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{vc};font-size:16px">{vl}</b><br>'
    f'<span style="font-size:12px;color:#64748b">AQL合格確率 {pa:.3f}（{np_}計画）</span></div>',
    unsafe_allow_html=True,
)

col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(
        visualize.oc_curve_chart(result["result_df"], result["oc_curves"]),
        use_container_width=True,
    )
with col_r:
    st.plotly_chart(visualize.protection_bar_chart(result["result_df"]), use_container_width=True)

st.subheader("検査計画 統計詳細")
display_df = result["result_df"].copy()
display_df.columns = [
    "ロットサイズ", "サンプルサイズ", "合格判定数", "AQL(%)",
    "Pa(AQL水準)", "Pa(RQL水準)", "保護スコア",
]
st.dataframe(display_df, use_container_width=True)

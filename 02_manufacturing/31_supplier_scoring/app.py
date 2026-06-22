"""仕入先品質複合スコアリング — 仕入先品質管理モニタリング。"""
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

st.set_page_config(page_title="仕入先品質スコアリング", page_icon="🏭", layout="wide")
st.markdown("""<style>
[data-testid="stAppViewContainer"]{background-color:#f5f7fa;}
[data-testid="stHeader"]{background-color:#f5f7fa;}
.block-container{padding-top:1rem;}
</style>""", unsafe_allow_html=True)
st.markdown('<div style="background:#1e3a5f;color:white;padding:12px 20px;border-radius:6px;margin-bottom:16px"><h3 style="margin:0;font-family:BIZ UDGothic">🏭 仕入先品質複合スコアリング（受入不良率 × Cpk × クレーム件数）</h3></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙ 設定")
    st.caption("CSV 列: supplier / defect_rate / cpk / claim_count")
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
        st.session_state.update({"result": result,
            "uploaded_name": uploaded.name if uploaded else "sample_supplier_scoring.csv",
            "row_count": len(df)})
    except ValueError as e:
        st.error(str(e)); st.stop()
    try:
        from _common.db_writer import init_db, write_upload, write_kpi
        init_db()
        uid = write_upload("supplier_scoring",
                           st.session_state.get("uploaded_name"),
                           st.session_state.get("row_count"))
        write_kpi(uid, "supplier_scoring", datetime.now().strftime("%Y-%m"),
                  "avg_score",
                  float(st.session_state["result"]["avg_total_score"]),
                  st.session_state["result"]["verdict"])
    except Exception as _e:
        st.caption(f"⚠ DB書き込みスキップ: {_e}")

result = st.session_state.get("result")
if not result:
    st.info("「▶ 分析実行」を押してください。"); st.stop()

avg  = result["avg_total_score"]
best = result["best_supplier"]
wrst = result["worst_supplier"]
n    = result["n_suppliers"]
vd   = result["verdict"]
_C   = {"good":"#16a34a","warning":"#d97706","alert":"#dc2626"}
_L   = {"good":"品質管理良好","warning":"要注意","alert":"要改善"}
vc, vl = _C[vd], _L[vd]

c1,c2,c3,c4 = st.columns(4)
c1.metric("平均品質スコア", f"{avg:.1f}点")
c2.metric("最優秀仕入先", best)
c3.metric("要改善仕入先", wrst)
c4.markdown(f'<div style="background:{vc}22;border-left:4px solid {vc};padding:8px 12px;border-radius:4px;margin-top:4px"><b style="color:{vc};font-size:16px">{vl}</b><br><span style="font-size:12px;color:#64748b">平均={avg:.1f}点</span></div>', unsafe_allow_html=True)

col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(visualize.score_bar_chart(result["result_df"]), use_container_width=True)
with col_r:
    st.plotly_chart(visualize.radar_chart(result["result_df"]), use_container_width=True)

st.subheader("仕入先別 スコア詳細")
display_df = result["result_df"][["supplier","defect_rate","cpk","claim_count","defect_score","cpk_score","claim_score","total_score"]].sort_values("total_score", ascending=False).reset_index(drop=True)
display_df.columns = ["仕入先","不良率(%)","Cpk","クレーム件数","不良率スコア","Cpkスコア","クレームスコア","合計スコア"]
st.dataframe(display_df, use_container_width=True)

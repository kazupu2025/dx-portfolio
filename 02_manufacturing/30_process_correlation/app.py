"""工程間品質相関分析 — 工程パラメータ vs 不良率 相関モニタリング。"""
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

st.set_page_config(page_title="工程間品質相関分析", page_icon="📈", layout="wide")
st.markdown("""<style>
[data-testid="stAppViewContainer"]{background-color:#f5f7fa;}
[data-testid="stHeader"]{background-color:#f5f7fa;}
.block-container{padding-top:1rem;}
</style>""", unsafe_allow_html=True)
st.markdown('<div style="background:#1e3a5f;color:white;padding:12px 20px;border-radius:6px;margin-bottom:16px"><h3 style="margin:0;font-family:BIZ UDGothic">📈 工程間品質相関分析（前工程パラメータ × 後工程不良率）</h3></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙ 設定")
    st.caption("CSV 列: month / [パラメータ列...] / defect_rate")
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
        st.session_state.update({"result": result, "df_clean": df,
            "uploaded_name": uploaded.name if uploaded else "sample_process_correlation.csv",
            "row_count": len(df)})
    except ValueError as e:
        st.error(str(e)); st.stop()
    try:
        from _common.db_writer import init_db, write_upload, write_kpi
        init_db()
        uid = write_upload("process_correlation",
                           st.session_state.get("uploaded_name"),
                           st.session_state.get("row_count"))
        write_kpi(uid, "process_correlation", datetime.now().strftime("%Y-%m"),
                  "max_corr",
                  float(st.session_state["result"]["max_abs_corr"]),
                  st.session_state["result"]["verdict"])
    except Exception as _e:
        st.caption(f"⚠ DB書き込みスキップ: {_e}")

result = st.session_state.get("result")
if not result:
    st.info("「▶ 分析実行」を押してください。"); st.stop()

mac  = result["max_abs_corr"]
sp   = result["strongest_param"]
nm   = result["n_months"]
vd   = result["verdict"]
_C   = {"good":"#16a34a","warning":"#d97706","alert":"#dc2626"}
_L   = {"good":"強相関検出","warning":"中程度相関","alert":"相関弱"}
vc, vl = _C[vd], _L[vd]

c1,c2,c3,c4 = st.columns(4)
c1.metric("最大|相関係数|", f"{mac:.3f}")
c2.metric("最強相関パラメータ", sp)
c3.metric("データ月数", f"{nm}ヶ月")
c4.markdown(f'<div style="background:{vc}22;border-left:4px solid {vc};padding:8px 12px;border-radius:4px;margin-top:4px"><b style="color:{vc};font-size:16px">{vl}</b><br><span style="font-size:12px;color:#64748b">|r|={mac:.3f}</span></div>', unsafe_allow_html=True)

col_l, col_r = st.columns(2)
df_clean = st.session_state.get("df_clean", df)
with col_l:
    st.plotly_chart(visualize.correlation_bar_chart(result["target_corr"]), use_container_width=True)
with col_r:
    st.plotly_chart(visualize.scatter_chart(df_clean, sp), use_container_width=True)

st.subheader("パラメータ別 相関係数・p値")
tc = result["target_corr"].copy()
tc["判定"] = tc.apply(lambda r: "✅ 有意・強" if abs(r["correlation"])>=0.7 and r["p_value"]<0.05
                      else ("⚠ 有意" if r["p_value"]<0.05 else "参考"), axis=1)
st.dataframe(tc, use_container_width=True)

st.subheader("相関行列")
st.dataframe(result["corr_df"].round(3), use_container_width=True)

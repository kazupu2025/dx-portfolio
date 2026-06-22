"""4M変更前後品質比較 — 変化点有意差検定モニタリング。"""
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

st.set_page_config(page_title="4M変更前後品質比較", page_icon="📊", layout="wide")
st.markdown("""<style>
[data-testid="stAppViewContainer"]{background-color:#f5f7fa;}
[data-testid="stHeader"]{background-color:#f5f7fa;}
.block-container{padding-top:1rem;}
</style>""", unsafe_allow_html=True)
st.markdown('<div style="background:#1e3a5f;color:white;padding:12px 20px;border-radius:6px;margin-bottom:16px"><h3 style="margin:0;font-family:BIZ UDGothic">📊 4M変更前後品質比較 — 変化点有意差検定</h3></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙ 設定")
    st.caption("CSV 列: change_id / change_name / group / value")
    st.caption("group = 変更前 or 変更後")
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
            "uploaded_name": uploaded.name if uploaded else "sample_4m_change_comparison.csv",
            "row_count": len(df)})
    except ValueError as e:
        st.error(str(e)); st.stop()
    try:
        from _common.db_writer import init_db, write_upload, write_kpi
        init_db()
        uid = write_upload("4m_change_comparison",
                           st.session_state.get("uploaded_name"),
                           st.session_state.get("row_count"))
        write_kpi(uid, "4m_change_comparison", datetime.now().strftime("%Y-%m"),
                  "significant_ratio",
                  float(st.session_state["result"]["significant_ratio"]),
                  st.session_state["result"]["verdict"])
    except Exception as _e:
        st.caption(f"⚠ DB書き込みスキップ: {_e}")

result = st.session_state.get("result")
if not result:
    st.info("「▶ 分析実行」を押してください。"); st.stop()

sr  = result["significant_ratio"]
sc  = result["significant_count"]
tc  = result["total_changes"]
bc  = result["best_change"]
vd  = result["verdict"]
_C  = {"good":"#16a34a","warning":"#d97706","alert":"#dc2626"}
_L  = {"good":"効果確認良好","warning":"要注意","alert":"要改善"}
vc, vl = _C[vd], _L[vd]

c1,c2,c3,c4 = st.columns(4)
c1.metric("変更効果確認率", f"{sr:.1f}%")
c2.metric("有意差あり件数", f"{sc}/{tc}件")
c3.metric("最大改善変更", bc)
c4.markdown(f'<div style="background:{vc}22;border-left:4px solid {vc};padding:8px 12px;border-radius:4px;margin-top:4px"><b style="color:{vc};font-size:16px">{vl}</b><br><span style="font-size:12px;color:#64748b">有意差確認率={sr:.1f}%</span></div>', unsafe_allow_html=True)

col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(visualize.pvalue_bar_chart(result["result_summary"]), use_container_width=True)
with col_r:
    st.plotly_chart(visualize.mean_comparison_chart(None, result["result_summary"]), use_container_width=True)

st.subheader("変更別 検定結果詳細")
display_df = result["result_summary"].copy()
display_df["判定"] = display_df["significant"].map({True:"✅ 有意差あり", False:"⚠ 差なし"})
display_df = display_df.drop(columns=["significant"])
st.dataframe(display_df, use_container_width=True)

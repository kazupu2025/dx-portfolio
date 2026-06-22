"""品質コストROI分析（予防投資額 vs 失敗コスト削減額）。"""
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

st.set_page_config(page_title="品質コストROI分析", page_icon="💹", layout="wide")
st.markdown("""<style>
[data-testid="stAppViewContainer"]{background-color:#f5f7fa;}
[data-testid="stHeader"]{background-color:#f5f7fa;}
.block-container{padding-top:1rem;}
</style>""", unsafe_allow_html=True)
st.markdown(
    '<div style="background:#1e3a5f;color:white;padding:12px 20px;border-radius:6px;margin-bottom:16px">'
    '<h3 style="margin:0;font-family:BIZ UDGothic">💹 品質コストROI分析 — 予防投資額 vs 失敗コスト削減額</h3></div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙ 設定")
    st.caption("CSV 列: month / prevention_cost / appraisal_cost / internal_failure / external_failure（単位: 万円）")
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
            "uploaded_name": uploaded.name if uploaded else "sample_quality_roi.csv",
            "row_count": len(df),
        })
    except ValueError as e:
        st.error(str(e))
        st.stop()
    try:
        from _common.db_writer import init_db, write_upload, write_kpi
        init_db()
        uid = write_upload("quality_roi", st.session_state.get("uploaded_name"), st.session_state.get("row_count"))
        write_kpi(uid, "quality_roi", datetime.now().strftime("%Y-%m"),
                  "roi",
                  float(st.session_state["result"]["roi"]),
                  st.session_state["result"]["verdict"])
    except Exception as _e:
        st.caption(f"⚠ DB書き込みスキップ: {_e}")

result = st.session_state.get("result")
if not result:
    st.info("「▶ 分析実行」を押してください。")
    st.stop()

roi  = result["roi"]
afr  = result["avg_failure_ratio"]
bm   = result["best_month"]
vd   = result["verdict"]
tv   = result["trend_verdict"]
_C   = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_L   = {"good": "ROI良好", "warning": "要改善", "alert": "逆効果"}
vc, vl = _C[vd], _L[vd]
trend_str = "↓ 減少傾向（改善中）" if tv else "↑ 増加傾向（要対策）"

c1, c2, c3, c4 = st.columns(4)
c1.metric("品質投資ROI", f"{roi:.1f}%")
c2.metric("平均失敗コスト比率", f"{afr:.1f}%")
c3.metric("最低失敗比率月", bm)
c4.markdown(
    f'<div style="background:{vc}22;border-left:4px solid {vc};padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{vc};font-size:16px">{vl}</b><br>'
    f'<span style="font-size:12px;color:#64748b">ROI {roi:.1f}% / {trend_str}</span></div>',
    unsafe_allow_html=True,
)

col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(visualize.cost_trend_chart(result["result_df"]), use_container_width=True)
with col_r:
    st.plotly_chart(visualize.failure_ratio_chart(result["result_df"]), use_container_width=True)

st.subheader("月次 品質コスト詳細")
display_df = result["result_df"][["month", "prevention_cost", "appraisal_cost",
                                   "internal_failure", "external_failure",
                                   "total_prevention", "total_failure", "total_cost", "failure_ratio"]].copy()
display_df.columns = ["年月", "予防コスト", "評価コスト", "内部失敗", "外部失敗",
                       "予防計", "失敗計", "品質コスト計", "失敗比率(%)"]
st.dataframe(display_df, use_container_width=True)

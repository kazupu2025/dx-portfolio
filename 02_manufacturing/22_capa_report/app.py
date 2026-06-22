"""CAPA 完了率・期限遵守率レポート — CAPA 管理状況モニタリング。"""
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

st.set_page_config(page_title="CAPA完了率・期限遵守率レポート", page_icon="✅", layout="wide")

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
    "✅ CAPA 完了率・期限遵守率レポート</h3>"
    "</div>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙ 設定")
    st.caption("CSV 列: month / total / completed / on_time_completed")
    uploaded   = st.file_uploader("CSVアップロード", type=["csv"])
    use_sample = st.button("サンプルデータを使用", use_container_width=True)

    if uploaded:
        st.session_state["df"] = pd.read_csv(uploaded)
    elif use_sample:
        st.session_state["df"] = generate_sample_csv()

    df: pd.DataFrame | None = st.session_state.get("df")
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
            "result":        result,
            "uploaded_name": uploaded.name if uploaded else "sample_capa_report.csv",
            "row_count":     len(df),
        })
    except ValueError as e:
        st.error(str(e))
        st.stop()

    try:
        from _common.db_writer import init_db, write_upload, write_kpi
        init_db()
        uid = write_upload(
            "capa_report",
            st.session_state.get("uploaded_name"),
            st.session_state.get("row_count"),
        )
        write_kpi(
            uid, "capa_report",
            datetime.now().strftime("%Y-%m"),
            "completion_rate",
            float(st.session_state["result"]["completion_rate"]),
            st.session_state["result"]["verdict"],
        )
    except Exception as _e:
        st.caption(f"⚠ DB書き込みスキップ: {_e}")

result = st.session_state.get("result")
if not result:
    st.info("「▶ 分析実行」を押してください。")
    st.stop()

avg_capas = result["avg_monthly_capas"]
comp_rate = result["completion_rate"]
ontime    = result["ontime_rate"]
verdict   = result["verdict"]

_COLOR = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_LABEL = {"good": "CAPA管理良好", "warning": "要注意", "alert": "要改善"}
v_color = _COLOR[verdict]
v_label = _LABEL[verdict]

c1, c2, c3, c4 = st.columns(4)
c1.metric("月次平均 CAPA 件数", f"{avg_capas:.1f}件")
c2.metric("完了率", f"{comp_rate:.1f}%")
c3.metric("期限遵守率", f"{ontime:.1f}%")
c4.markdown(
    f'<div style="background:{v_color}22;border-left:4px solid {v_color};'
    f'padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{v_color};font-size:16px">{v_label}</b><br>'
    f'<span style="font-size:12px;color:#64748b">完了率={comp_rate:.1f}%</span>'
    f'</div>',
    unsafe_allow_html=True,
)

col_l, col_r = st.columns([2, 1])
with col_l:
    st.plotly_chart(
        visualize.rate_trend_chart(result["result_df"]),
        use_container_width=True,
    )
with col_r:
    st.plotly_chart(
        visualize.monthly_bar_chart(result["result_df"]),
        use_container_width=True,
    )

st.subheader("CAPA 実績詳細")
display_df = (
    result["result_df"][["month", "total", "completed", "on_time_completed"]]
    .sort_values("month")
    .reset_index(drop=True)
)
display_df["完了率(%)"] = (display_df["completed"] / display_df["total"] * 100).round(1)
display_df["遵守率(%)"] = (display_df["on_time_completed"] / display_df["total"] * 100).round(1)
st.dataframe(display_df, use_container_width=True)

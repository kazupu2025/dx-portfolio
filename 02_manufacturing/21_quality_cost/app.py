"""品質コスト明細集計（4分類）— 損失コスト比率 × 月次トレンド可視化。"""
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

st.set_page_config(page_title="品質コスト明細集計（4分類）", page_icon="💴", layout="wide")

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
    "💴 品質コスト明細集計（4分類）</h3>"
    "</div>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙ 設定")
    st.caption("CSV 列: month / category / amount")
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
            "uploaded_name": uploaded.name if uploaded else "sample_quality_cost.csv",
            "row_count":     len(df),
        })
    except ValueError as e:
        st.error(str(e))
        st.stop()

    try:
        from _common.db_writer import init_db, write_upload, write_kpi
        init_db()
        uid = write_upload(
            "quality_cost",
            st.session_state.get("uploaded_name"),
            st.session_state.get("row_count"),
        )
        write_kpi(
            uid, "quality_cost",
            datetime.now().strftime("%Y-%m"),
            "failure_ratio",
            float(st.session_state["result"]["failure_ratio"]),
            st.session_state["result"]["verdict"],
        )
    except Exception as _e:
        st.caption(f"⚠ DB書き込みスキップ: {_e}")

result = st.session_state.get("result")
if not result:
    st.info("「▶ 分析実行」を押してください。")
    st.stop()

avg_cost = result["avg_monthly_cost"]
dom_cat  = result["dominant_category"]
ratio    = result["failure_ratio"]
verdict  = result["verdict"]

_COLOR = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_LABEL = {"good": "品質管理良好", "warning": "要注意", "alert": "要改善"}
v_color = _COLOR[verdict]
v_label = _LABEL[verdict]

c1, c2, c3, c4 = st.columns(4)
c1.metric("月次平均コスト", f"¥{avg_cost:,.0f}")
c2.metric("最大コスト分類", dom_cat)
c3.metric("損失コスト比率", f"{ratio:.1f}%")
c4.markdown(
    f'<div style="background:{v_color}22;border-left:4px solid {v_color};'
    f'padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{v_color};font-size:16px">{v_label}</b><br>'
    f'<span style="font-size:12px;color:#64748b">損失比率={ratio:.1f}%</span>'
    f'</div>',
    unsafe_allow_html=True,
)

col_l, col_r = st.columns([2, 1])
with col_l:
    st.plotly_chart(
        visualize.monthly_cost_chart(result["result_df"]),
        use_container_width=True,
    )
with col_r:
    st.plotly_chart(
        visualize.category_bar_chart(result["result_df"]),
        use_container_width=True,
    )

st.subheader("品質コスト詳細")
display_df = (
    result["result_df"][["month", "category", "amount"]]
    .sort_values(["month", "category"])
    .reset_index(drop=True)
)
display_df["amount"] = display_df["amount"].apply(lambda v: f"¥{int(v):,}")
st.dataframe(display_df, use_container_width=True)

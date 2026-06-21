"""不良モード別パレート × 時系列複合分析。"""
from __future__ import annotations
import sys
from pathlib import Path

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import analyze
import visualize
from sample_data import generate_sample_csv

st.set_page_config(page_title="不良モード別パレート分析", page_icon="📊", layout="wide")

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
    '📊 不良モード別パレート × 時系列複合分析</h3>'
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

    date_col = mode_col = count_col = None
    run_btn = False

    if df is not None:
        cols      = df.columns.tolist()
        date_col  = st.selectbox("年月列",       cols, key="date_col")
        mode_col  = st.selectbox("不良モード列", cols, index=min(1, len(cols) - 1), key="mode_col")
        count_col = st.selectbox("件数列",       cols, index=min(2, len(cols) - 1), key="count_col")
        run_btn   = st.button("▶ 分析実行", type="primary", use_container_width=True)

# ── Main area ──────────────────────────────────────────────────────
if df is None:
    st.info("サイドバーから CSV をアップロードするか、「サンプルデータを使用」をクリックしてください。")
    st.stop()

if run_btn:
    if not all([date_col, mode_col, count_col]):
        st.error("列をすべて選択してください。")
        st.stop()
    try:
        result = analyze.run_analysis(df, date_col, mode_col, count_col)
        st.session_state.update({
            "result":        result,
            "date_col":      date_col,
            "mode_col":      mode_col,
            "count_col":     count_col,
            "uploaded_name": uploaded.name if uploaded else "sample_defect_pareto.csv",
            "row_count":     len(df),
        })
    except ValueError as e:
        st.error(str(e))
        st.stop()

result    = st.session_state.get("result")
date_col  = st.session_state.get("date_col",  date_col)
mode_col  = st.session_state.get("mode_col",  mode_col)
count_col = st.session_state.get("count_col", count_col)

if not result:
    st.info("サイドバーで設定を選択し、「▶ 分析実行」を押してください。")
    st.stop()

# ── KPI サマリー（4列）───────────────────────────────────────────
verdict = result["verdict"]
_COLOR  = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_LABEL  = {"good": "改善中",  "warning": "横ばい",  "alert": "悪化"}
v_color = _COLOR[verdict]
v_label = _LABEL[verdict]

c1, c2, c3, c4 = st.columns(4)
c1.metric("全期間合計件数", f"{result['total_count']:,}件")
c2.metric("最多不良モード", f"{result['top_mode']}（{result['top_mode_pct']:.1f}%）")
c3.metric("vital few",     f"{len(result['vital_few'])}モードで80%超")
c4.markdown(
    f'<div style="background:{v_color}22;border-left:4px solid {v_color};'
    f'padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{v_color};font-size:16px">{v_label}</b><br>'
    f'<span style="font-size:12px;color:#64748b">'
    f'{result["latest_month"]}：{result["latest_total"]}件 '
    f'（前月 {result["prev_total"]}件）</span></div>',
    unsafe_allow_html=True,
)

# ── チャート ──────────────────────────────────────────────────────
col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(
        visualize.pareto_chart(result["pareto_df"], mode_col, result["vital_few"]),
        use_container_width=True,
    )
with col_r:
    st.plotly_chart(
        visualize.trend_chart(result["trend_df"]),
        use_container_width=True,
    )

# ── パレートデータテーブル ─────────────────────────────────────────
st.subheader("パレート集計テーブル")
display_df = result["pareto_df"].copy()
display_df["cumulative_pct"] = display_df["cumulative_pct"].map(lambda x: f"{x:.1f}%")
display_df["vital_few"] = display_df[mode_col].apply(
    lambda m: "★" if m in result["vital_few"] else ""
)
st.dataframe(display_df, hide_index=True, use_container_width=True)

# ── DB 書き込み（失敗してもアプリは継続）────────────────────────
try:
    from _common.db_writer import init_db, write_upload, write_kpi
    init_db()
    uid = write_upload(
        "defect_pareto",
        st.session_state.get("uploaded_name"),
        st.session_state.get("row_count"),
    )
    write_kpi(
        uid, "defect_pareto",
        result["latest_month"],
        "top_mode_pct", result["top_mode_pct"], verdict,
    )
except Exception as _e:
    st.caption(f"⚠ DB書き込みスキップ: {_e}")

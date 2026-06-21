"""品質コストROI分析 — PAFモデル × 月次改善効果測定。"""
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

st.set_page_config(page_title="品質コストROI分析", page_icon="💹", layout="wide")

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
    "💹 品質コストROI分析 — PAFモデル × 月次改善効果測定</h3>"
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
    run_btn = False
    if df is not None:
        run_btn = st.button("▶ 分析実行", type="primary", use_container_width=True)

# ── Main area ──────────────────────────────────────────────────────
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

result = st.session_state.get("result")
if not result:
    st.info("「▶ 分析実行」を押してください。")
    st.stop()

# ── KPI 4列 ────────────────────────────────────────────────────────
latest_roi    = result["latest_roi"]
failure_ratio = result["failure_ratio"]
verdict       = result["verdict"]

_COLOR = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_LABEL = {"good": "投資回収済み", "warning": "改善中", "alert": "要投資見直し"}
v_color = _COLOR[verdict]
v_label = _LABEL[verdict]

sorted_df      = df.sort_values("month").reset_index(drop=True)
latest_failure = float(sorted_df["failure_cost"].iloc[-1])
first_failure  = float(sorted_df["failure_cost"].iloc[0])
delta_failure  = first_failure - latest_failure  # 正=改善

c1, c2, c3, c4 = st.columns(4)
c1.metric("最新月 failure コスト", f"¥{latest_failure:,.0f}")
if latest_roi is not None:
    c2.metric("最新月 ROI", f"{latest_roi:.2f}x")
else:
    c2.metric("failure 比率（1行）", f"{failure_ratio:.1%}")
c3.metric(
    "failure 削減額（初月比）",
    f"¥{abs(delta_failure):,.0f}",
    delta=f"{'改善' if delta_failure >= 0 else '悪化'} ¥{abs(delta_failure):,.0f}",
)
c4.markdown(
    f'<div style="background:{v_color}22;border-left:4px solid {v_color};'
    f'padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{v_color};font-size:16px">{v_label}</b><br>'
    f'<span style="font-size:12px;color:#64748b">'
    + (f"ROI={latest_roi:.2f}x" if latest_roi is not None else f"ratio={failure_ratio:.1%}")
    + "</span></div>",
    unsafe_allow_html=True,
)

# ── チャート ──────────────────────────────────────────────────────
col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(visualize.cost_bar_chart(sorted_df), use_container_width=True)
with col_r:
    if latest_roi is not None:
        st.plotly_chart(
            visualize.roi_line_chart(sorted_df, result["roi_series"]),
            use_container_width=True,
        )
    else:
        st.info("ROI 推移グラフには 2 ヶ月以上のデータが必要です。")

# ── DB 書き込み ────────────────────────────────────────────────────
try:
    from _common.db_writer import init_db, write_upload, write_kpi
    init_db()
    uid = write_upload(
        "quality_cost_roi",
        st.session_state.get("uploaded_name"),
        st.session_state.get("row_count"),
    )
    value = latest_roi if latest_roi is not None else failure_ratio
    write_kpi(
        uid, "quality_cost_roi",
        datetime.now().strftime("%Y-%m"),
        "roi", value, verdict,
    )
except Exception as _e:
    st.caption(f"⚠ DB書き込みスキップ: {_e}")

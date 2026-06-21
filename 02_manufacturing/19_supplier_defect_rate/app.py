"""協力会社別受入不良率月報 — 月次受入検査 × 不良率自動計算 × 協力会社ランク。"""
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

st.set_page_config(page_title="協力会社別受入不良率月報", page_icon="🏭", layout="wide")

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
    "🏭 協力会社別受入不良率月報 — 月次受入検査 × 不良率自動計算</h3>"
    "</div>",
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙ 設定")
    st.caption("CSV 列: supplier / month / incoming_qty / defect_qty")
    uploaded   = st.file_uploader("CSVアップロード", type=["csv"])
    use_sample = st.button("サンプルデータを使用", use_container_width=True)

    if use_sample:
        st.session_state["df"] = generate_sample_csv()
    elif uploaded:
        st.session_state["df"] = pd.read_csv(uploaded)

    df: pd.DataFrame | None = st.session_state.get("df")
    run_btn = False
    if df is not None:
        run_btn = st.button("▶ 分析実行", type="primary", use_container_width=True)

# ── Main ──────────────────────────────────────────────────────────
if df is None:
    st.info("サイドバーから CSV をアップロードするか、「サンプルデータを使用」をクリックしてください。")
    st.stop()

if run_btn:
    try:
        result = analyze.run_analysis(df)
        st.session_state.update({
            "result":        result,
            "uploaded_name": uploaded.name if uploaded else "sample_supplier_defect_rate.csv",
            "row_count":     len(df),
        })
    except ValueError as e:
        st.error(str(e))
        st.stop()

    # DB書き込み（run_btn ガード内 — 分析実行時のみ実行）
    try:
        from _common.db_writer import init_db, write_upload, write_kpi
        init_db()
        uid = write_upload(
            "supplier_defect_rate",
            st.session_state.get("uploaded_name"),
            st.session_state.get("row_count"),
        )
        avg_for_db = st.session_state["result"]["avg_defect_rate"]
        verdict_for_db = st.session_state["result"]["verdict"]
        write_kpi(
            uid, "supplier_defect_rate",
            datetime.now().strftime("%Y-%m"),
            "defect_rate", avg_for_db, verdict_for_db,
        )
    except Exception as _e:
        st.caption(f"⚠ DB書き込みスキップ: {_e}")

result = st.session_state.get("result")
if not result:
    st.info("「▶ 分析実行」を押してください。")
    st.stop()

# ── KPI 4列 ────────────────────────────────────────────────────────
avg   = result["avg_defect_rate"]
best  = result["best_supplier"]
verdict = result["verdict"]

_COLOR = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_LABEL = {"good": "品質良好", "warning": "要注意", "alert": "要改善"}
v_color = _COLOR[verdict]
v_label = _LABEL[verdict]

c1, c2, c3, c4 = st.columns(4)
c1.metric("協力会社数", f"{result['n_suppliers']}社")
c2.metric("平均不良率", f"{avg:.2f}%")
c3.metric("最良協力会社", best)
c4.markdown(
    f'<div style="background:{v_color}22;border-left:4px solid {v_color};'
    f'padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{v_color};font-size:16px">{v_label}</b><br>'
    f'<span style="font-size:12px;color:#64748b">avg={avg:.2f}%</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# ── チャート ──────────────────────────────────────────────────────
col_l, col_r = st.columns([2, 1])
with col_l:
    st.plotly_chart(
        visualize.defect_rate_chart(result["result_df"]),
        use_container_width=True,
    )
with col_r:
    st.plotly_chart(
        visualize.supplier_bar_chart(result["result_df"]),
        use_container_width=True,
    )

# ── テーブル ──────────────────────────────────────────────────────
st.subheader("受入検査データ詳細")
display_df = result["result_df"][
    ["supplier", "month", "incoming_qty", "defect_qty", "defect_rate"]
].sort_values(["month", "supplier"]).reset_index(drop=True)
st.dataframe(display_df, use_container_width=True)

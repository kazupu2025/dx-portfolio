"""仕入先品質複合スコアリング — 重み付き合成スコア × 仕入先ランク。"""
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

st.set_page_config(page_title="仕入先品質複合スコアリング", page_icon="🏭", layout="wide")

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
    "🏭 仕入先品質複合スコアリング — 重み付き合成スコア × 仕入先ランク</h3>"
    "</div>",
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙ 設定")
    st.caption("重み: 不良率 50% / 納期 30% / 価格偏差 20%")
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
            "uploaded_name": uploaded.name if uploaded else "sample_supplier_scoring.csv",
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
avg_score      = result["avg_score"]
best_supplier  = result["best_supplier"]
verdict        = result["verdict"]
scored_df      = result["scored_df"]

_COLOR = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_LABEL = {"good": "優良仕入先多数", "warning": "改善余地あり", "alert": "取引見直し検討"}
v_color = _COLOR[verdict]
v_label = _LABEL[verdict]

best_score = float(scored_df.loc[scored_df["supplier_id"] == best_supplier, "composite_score"].iloc[0])

c1, c2, c3, c4 = st.columns(4)
c1.metric("仕入先数", f"{result['n_suppliers']}社")
c2.metric("平均合成スコア", f"{avg_score:.1f}点")
c3.metric("最優良仕入先", best_supplier, delta=f"{best_score:.1f}点")
c4.markdown(
    f'<div style="background:{v_color}22;border-left:4px solid {v_color};'
    f'padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{v_color};font-size:16px">{v_label}</b><br>'
    f'<span style="font-size:12px;color:#64748b">avg={avg_score:.1f}点</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# ── チャート ──────────────────────────────────────────────────────
col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(visualize.score_bar_chart(scored_df), use_container_width=True)
with col_r:
    st.plotly_chart(visualize.breakdown_chart(scored_df), use_container_width=True)

# ── テーブル ──────────────────────────────────────────────────────
st.subheader("仕入先別スコア詳細")
display_cols = [
    "supplier_id", "defect_rate", "delivery_rate", "price_variance",
    "composite_score", "verdict",
]
st.dataframe(
    scored_df[display_cols].sort_values("composite_score", ascending=False).reset_index(drop=True),
    use_container_width=True,
)

# ── DB 書き込み ────────────────────────────────────────────────────
try:
    from _common.db_writer import init_db, write_upload, write_kpi
    init_db()
    uid = write_upload(
        "supplier_scoring",
        st.session_state.get("uploaded_name"),
        st.session_state.get("row_count"),
    )
    write_kpi(
        uid, "supplier_scoring",
        datetime.now().strftime("%Y-%m"),
        "avg_score", avg_score, verdict,
    )
except Exception as _e:
    st.caption(f"⚠ DB書き込みスキップ: {_e}")

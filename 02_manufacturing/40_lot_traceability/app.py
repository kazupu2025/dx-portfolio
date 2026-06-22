"""ロット完全トレーサビリティ — 原材料 → 工程 → 出荷先 グラフ可視化。"""
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

st.set_page_config(
    page_title="ロットトレーサビリティ", page_icon="🔍", layout="wide"
)
st.markdown(
    """<style>
[data-testid="stAppViewContainer"]{background-color:#f5f7fa;}
[data-testid="stHeader"]{background-color:#f5f7fa;}
.block-container{padding-top:1rem;}
</style>""",
    unsafe_allow_html=True,
)
st.markdown(
    '<div style="background:#1e3a5f;color:white;padding:12px 20px;border-radius:6px;margin-bottom:16px"><h3 style="margin:0;font-family:BIZ UDGothic">🔍 ロット完全トレーサビリティ（双方向追跡）</h3></div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙ 設定")
    st.caption("CSV 列: from_node / to_node / edge_type / lot_id / quantity")
    uploaded = st.file_uploader("CSVアップロード", type=["csv"])
    use_sample = st.button("サンプルデータを使用", use_container_width=True)
    if uploaded:
        st.session_state["df"] = pd.read_csv(uploaded)
    elif use_sample:
        st.session_state["df"] = generate_sample_csv()
    df = st.session_state.get("df")
    run_btn = False
    if df is not None:
        run_btn = st.button("▶ グラフ構築", type="primary", use_container_width=True)

if df is None:
    st.info(
        "サイドバーから CSV をアップロードするか、「サンプルデータを使用」をクリックしてください。"
    )
    st.stop()

if run_btn:
    try:
        result = analyze.run_analysis(df)
        st.session_state.update(
            {
                "result": result,
                "df_raw": df,
                "uploaded_name": uploaded.name if uploaded else "sample_lot_traceability.csv",
                "row_count": len(df),
            }
        )
    except ValueError as e:
        st.error(str(e))
        st.stop()
    try:
        from _common.db_writer import init_db, write_upload, write_kpi

        init_db()
        uid = write_upload(
            "lot_traceability",
            st.session_state.get("uploaded_name"),
            st.session_state.get("row_count"),
        )
        write_kpi(
            uid,
            "lot_traceability",
            datetime.now().strftime("%Y-%m"),
            "n_lots",
            float(st.session_state["result"]["n_lots"]),
            st.session_state["result"]["verdict"],
        )
    except Exception as _e:
        st.caption(f"⚠ DB書き込みスキップ: {_e}")

result = st.session_state.get("result")
if not result:
    st.info("「▶ グラフ構築」を押してください。")
    st.stop()

nn = result["n_nodes"]
ne = result["n_edges"]
nl = result["n_lots"]
vd = result["verdict"]
_C = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_L = {"good": "追跡良好", "warning": "複雑化注意", "alert": "構造複雑"}
vc, vl = _C[vd], _L[vd]

c1, c2, c3, c4 = st.columns(4)
c1.metric("ノード数", f"{nn}")
c2.metric("エッジ数", f"{ne}")
c3.metric("管理ロット数", f"{nl}件")
c4.markdown(
    f'<div style="background:{vc}22;border-left:4px solid {vc};padding:8px 12px;border-radius:4px;margin-top:4px"><b style="color:{vc};font-size:16px">{vl}</b></div>',
    unsafe_allow_html=True,
)

st.plotly_chart(
    visualize.traceability_graph(
        result["G"], result["material_nodes"], result["destination_nodes"]
    ),
    use_container_width=True,
)

st.subheader("🔎 ロット別追跡")
df_raw = st.session_state.get("df_raw", df)
lot_ids = sorted(df_raw["lot_id"].unique().tolist())
selected_lot = st.selectbox("追跡するロット", lot_ids)
if selected_lot:
    st.plotly_chart(
        visualize.lot_edge_table(df_raw, selected_lot), use_container_width=True
    )
    lot_nodes = set(df_raw[df_raw["lot_id"] == selected_lot]["from_node"].tolist()) | set(
        df_raw[df_raw["lot_id"] == selected_lot]["to_node"].tolist()
    )
    st.info(
        f"ロット **{selected_lot}** は {len(lot_nodes)} ノードを経由しています: "
        + " → ".join(sorted(lot_nodes))
    )

st.subheader("CSV データ一覧")
st.dataframe(df_raw, use_container_width=True)

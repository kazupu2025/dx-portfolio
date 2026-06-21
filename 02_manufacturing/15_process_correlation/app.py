"""工程間品質相関分析 — Pearson 相関行列 × ヒートマップ。"""
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

st.set_page_config(page_title="工程間品質相関分析", page_icon="📊", layout="wide")

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
    '📊 工程間品質相関分析 — Pearson 相関行列 × ヒートマップ</h3>'
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

    process_cols: list[str] = []
    run_btn = False

    if df is not None:
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if not numeric_cols:
            st.error("数値列が見つかりません。")
        else:
            process_cols = st.multiselect(
                "工程列を選択（2列以上）",
                numeric_cols,
                default=numeric_cols,
                key="process_cols",
            )
        run_btn = st.button("▶ 分析実行", type="primary", use_container_width=True)

# ── Main area ──────────────────────────────────────────────────────
if df is None:
    st.info("サイドバーから CSV をアップロードするか、「サンプルデータを使用」をクリックしてください。")
    st.stop()

if run_btn:
    if len(process_cols) < 2:
        st.error("工程列を 2 列以上選択してください。")
        st.stop()
    try:
        result = analyze.run_analysis(df, process_cols)
        st.session_state.update({
            "result":        result,
            "process_cols":  process_cols,
            "uploaded_name": uploaded.name if uploaded else "sample_process_correlation.csv",
            "row_count":     len(df),
        })
    except ValueError as e:
        st.error(str(e))
        st.stop()

result       = st.session_state.get("result")
process_cols = st.session_state.get("process_cols", process_cols)

if not result:
    st.info("サイドバーで工程列を選択し、「▶ 分析実行」を押してください。")
    st.stop()

# ── KPI サマリー（4列）───────────────────────────────────────────
max_abs_r = result["max_abs_r"]
top_pair  = result["top_pair"]
top_r     = result["top_r"]
verdict   = result["verdict"]

_COLOR = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_LABEL = {"good": "強い相関あり", "warning": "中程度の相関", "alert": "相関なし"}
v_color = _COLOR[verdict]
v_label = _LABEL[verdict]

c1, c2, c3, c4 = st.columns(4)
c1.metric("有効サンプル数", f"{result['n_samples']}件")
c2.metric("工程数", f"{result['n_processes']}工程")
c3.metric(
    "最強相関ペア",
    f"{top_pair[0]} × {top_pair[1]}",
    delta=f"r={top_r:.3f}",
)
c4.markdown(
    f'<div style="background:{v_color}22;border-left:4px solid {v_color};'
    f'padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{v_color};font-size:16px">{v_label}</b><br>'
    f'<span style="font-size:12px;color:#64748b">max |r|={max_abs_r:.3f}</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# ── チャート ──────────────────────────────────────────────────────
col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(
        visualize.heatmap_chart(result["corr_df"], result["pvalue_df"]),
        use_container_width=True,
    )
with col_r:
    st.plotly_chart(
        visualize.scatter_chart(
            df[process_cols],
            top_pair[0], top_pair[1],
            top_r, result["top_pvalue"],
        ),
        use_container_width=True,
    )

# ── 相関行列テーブル（p値付き）───────────────────────────────────
st.subheader("相関行列詳細（* p < 0.05）")
corr_display = result["corr_df"].copy()
pval_display = result["pvalue_df"]

rows = []
for i, col1 in enumerate(process_cols):
    row = {"工程": col1}
    for col2 in process_cols:
        r_val = corr_display.loc[col1, col2]
        p_val = pval_display.loc[col1, col2]
        cell = f"{r_val:.3f}"
        if col1 != col2 and p_val < 0.05:
            cell += "*"
        row[col2] = cell
    rows.append(row)

st.dataframe(pd.DataFrame(rows).set_index("工程"), use_container_width=True)

# ── DB 書き込み（失敗してもアプリは継続）────────────────────────
try:
    from _common.db_writer import init_db, write_upload, write_kpi
    init_db()
    uid = write_upload(
        "process_correlation",
        st.session_state.get("uploaded_name"),
        st.session_state.get("row_count"),
    )
    write_kpi(
        uid, "process_correlation",
        datetime.now().strftime("%Y-%m"),
        "max_r", max_abs_r, verdict,
    )
except Exception as _e:
    st.caption(f"⚠ DB書き込みスキップ: {_e}")

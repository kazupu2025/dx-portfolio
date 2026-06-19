"""SPC 管理図アプリ — X-bar/R + 異常8ルール自動検出。"""
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
import rules
import visualize
from sample_data import generate_sample_csv

st.set_page_config(page_title="SPC管理図", page_icon="📊", layout="wide")

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
    '<h3 style="margin:0;font-family:BIZ UDGothic">📊 SPC管理図 — X-bar/R + 異常8ルール自動検出</h3>'
    "</div>",
    unsafe_allow_html=True,
)

RULE_NAMES = {
    1: "Rule 1: 3σ超過",
    2: "Rule 2: 3点中2点が同側2σ外",
    3: "Rule 3: 5点中4点が同側1σ外",
    4: "Rule 4: 8点連続で同側",
    5: "Rule 5: 6点連続トレンド",
    6: "Rule 6: 14点交互",
    7: "Rule 7: 15点±1σ内（ハガーリング）",
    8: "Rule 8: 8点全て±1σ外（両側混在）",
}

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

    process_col = value_col = sub_col = process = None
    run_btn = False

    if df is not None:
        cols        = df.columns.tolist()
        process_col = st.selectbox("工程列",           cols, key="process_col")
        value_col   = st.selectbox("測定値列",         cols, index=min(2, len(cols)-1), key="value_col")
        sub_col     = st.selectbox("サブグループ列",   cols, index=0, key="sub_col")
        processes   = df[process_col].unique().tolist() if process_col else []
        process     = st.selectbox("分析する工程",     processes, key="process")
        run_btn     = st.button("▶ 分析実行", type="primary", use_container_width=True)

# ── Main area ──────────────────────────────────────────────────────
if df is None:
    st.info("サイドバーから CSV をアップロードするか、「サンプルデータを使用」をクリックしてください。")
    st.stop()

if run_btn:
    subset = df[df[process_col] == process]
    try:
        result       = analyze.run_analysis(subset, value_col, sub_col)
        xbar_list    = [s["xbar"] for s in result["subgroups"]]
        r_list       = [s["r"]    for s in result["subgroups"]]
        violations   = rules.detect_violations(xbar_list, result["xbar_cl"], result["sigma"])
        violations_r = rules.rule1_r(r_list, result["r_ucl"])
        st.session_state.update({
            "result": result, "violations": violations,
            "violations_r": violations_r, "proc_label": process,
            "uploaded_name": uploaded.name if uploaded else "sample_spc.csv",
            "row_count": len(df),
        })
    except ValueError as e:
        st.error(str(e))
        st.stop()

result       = st.session_state.get("result")
violations   = st.session_state.get("violations", {})
violations_r = st.session_state.get("violations_r", [])
proc_label   = st.session_state.get("proc_label", "")

if not result:
    st.info("サイドバーで設定を選択し、「▶ 分析実行」を押してください。")
    st.stop()

# KPI サマリー
all_violated = set(idx for v in violations.values() for idx in v)
total_sg     = len(result["subgroups"])
pct          = len(all_violated) / total_sg * 100 if total_sg else 0.0
v_color      = "#16a34a" if pct < 5 else "#d97706" if pct < 10 else "#dc2626"
v_label      = "安定" if pct < 5 else "要注意" if pct < 10 else "要確認"

c1, c2, c3, c4 = st.columns(4)
c1.metric("工程",          proc_label)
c2.metric("サブグループ数", total_sg)
c3.metric("逸脱率",        f"{pct:.1f}%")
c4.markdown(
    f'<div style="background:{v_color}22;border-left:4px solid {v_color};'
    f'padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{v_color};font-size:16px">{v_label}</b></div>',
    unsafe_allow_html=True,
)

# 管理図
st.plotly_chart(visualize.xbar_chart(result, violations),   use_container_width=True)
st.plotly_chart(visualize.r_chart(result, violations_r),    use_container_width=True)

# 違反テーブル
all_rows = [
    {"ルール": RULE_NAMES[rn], "サブグループ": result["subgroups"][i]["label"],
     "X̄値": f"{result['subgroups'][i]['xbar']:.4f}"}
    for rn, idxs in violations.items() for i in idxs
] + [
    {"ルール": "R-Rule 1: R が UCL 超過",
     "サブグループ": result["subgroups"][i]["label"],
     "X̄値": f"{result['subgroups'][i]['r']:.4f} (R値)"}
    for i in violations_r
]
if all_rows:
    st.subheader("⚠ 違反ポイント一覧")
    st.dataframe(pd.DataFrame(all_rows), hide_index=True, use_container_width=True)

# DB 書き込み（失敗してもアプリは継続）
try:
    from _common.db_writer import init_db, write_upload, write_kpi
    init_db()
    uid     = write_upload("spc", st.session_state.get("uploaded_name"), st.session_state.get("row_count"))
    verdict = "good" if pct < 5 else "warning" if pct < 10 else "alert"
    write_kpi(uid, "spc", datetime.now().strftime("%Y-%m"), "out_of_control_pct", pct, verdict)
except Exception as _e:
    st.caption(f"⚠ DB書き込みスキップ: {_e}")

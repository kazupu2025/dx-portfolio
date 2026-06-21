"""是正処置（8D）効果検証 — 統計的有意差検定（t検定/Mann-Whitney）。"""
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

# C-66 の visualize.py を転用
_C66 = Path(__file__).parent.parent / "12_4m_change"
if str(_C66) not in sys.path:
    sys.path.insert(0, str(_C66))

import analyze
import visualize
from sample_data import generate_sample_csv

st.set_page_config(page_title="是正処置効果検証", page_icon="📊", layout="wide")

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
    '📊 是正処置（8D）効果検証 — 統計的有意差検定（t検定/Mann-Whitney）</h3>'
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

    group_col = value_col = before_label = after_label = None
    run_btn = False

    if df is not None:
        cols      = df.columns.tolist()
        group_col = st.selectbox("グループ列", cols, key="group_col")
        value_col = st.selectbox("測定値列",   cols, index=min(1, len(cols) - 1), key="value_col")

        if group_col and group_col in df.columns:
            unique_vals  = sorted(df[group_col].dropna().unique().tolist())
            before_label = st.selectbox(
                "是正前ラベル", unique_vals, index=0, key="before_label"
            )
            after_label = st.selectbox(
                "是正後ラベル", unique_vals,
                index=min(1, len(unique_vals) - 1), key="after_label"
            )

        run_btn = st.button("▶ 分析実行", type="primary", use_container_width=True)

# ── Main area ──────────────────────────────────────────────────────
if df is None:
    st.info("サイドバーから CSV をアップロードするか、「サンプルデータを使用」をクリックしてください。")
    st.stop()

if run_btn:
    if not all([group_col, value_col, before_label, after_label]):
        st.error("列とラベルをすべて選択してください。")
        st.stop()
    if before_label == after_label:
        st.error("是正前ラベルと是正後ラベルは別の値を選択してください。")
        st.stop()
    try:
        result = analyze.run_analysis(df, group_col, value_col, before_label, after_label)
        st.session_state.update({
            "result":       result,
            "group_col":    group_col,
            "value_col":    value_col,
            "before_label": before_label,
            "after_label":  after_label,
            "uploaded_name": uploaded.name if uploaded else "sample_corrective_action.csv",
            "row_count": len(df),
        })
    except ValueError as e:
        st.error(str(e))
        st.stop()

result       = st.session_state.get("result")
group_col    = st.session_state.get("group_col",    group_col)
value_col    = st.session_state.get("value_col",    value_col)
before_label = st.session_state.get("before_label", before_label)
after_label  = st.session_state.get("after_label",  after_label)

if not result:
    st.info("サイドバーで設定を選択し、「▶ 分析実行」を押してください。")
    st.stop()

# ── KPI サマリー（4列）───────────────────────────────────────────
p_val   = result["p_value"]
eff     = result["effect_size"]
rec     = "t検定（Welch）" if result["recommended"] == "t" else "Mann-Whitney U"
verdict = result["verdict"]

_COLOR = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_LABEL = {"good": "是正効果確認", "warning": "軽微な効果", "alert": "効果不明"}
v_color = _COLOR[verdict]
v_label = _LABEL[verdict]

c1, c2, c3, c4 = st.columns(4)
c1.metric("p値（推奨検定）", f"{p_val:.4f}")
c2.metric("効果量", f"{eff:.3f}")
c3.metric("推奨検定", rec)
c4.markdown(
    f'<div style="background:{v_color}22;border-left:4px solid {v_color};'
    f'padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{v_color};font-size:16px">{v_label}</b><br>'
    f'<span style="font-size:12px;color:#64748b">'
    f'n前={result["n_before"]} / n後={result["n_after"]}'
    f'</span></div>',
    unsafe_allow_html=True,
)

# ── チャート（C-66 の visualize.py を転用）───────────────────────
before_arr = pd.to_numeric(
    df[df[group_col] == before_label][value_col], errors="coerce"
).dropna().to_numpy(dtype=float)
after_arr = pd.to_numeric(
    df[df[group_col] == after_label][value_col], errors="coerce"
).dropna().to_numpy(dtype=float)

col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(
        visualize.hist_chart(before_arr, after_arr, before_label, after_label),
        use_container_width=True,
    )
with col_r:
    st.plotly_chart(
        visualize.box_chart(before_arr, after_arr, before_label, after_label),
        use_container_width=True,
    )

# ── 検定結果テーブル ──────────────────────────────────────────────
st.subheader("検定結果詳細")

_star = lambda rec_val: "★ 推奨" if result["recommended"] == rec_val else "—"
table_df = pd.DataFrame([
    {
        "検定手法": "t検定（Welch）",
        "統計量": f"{result['t_stat']:.4f}",
        "p値": f"{result['t_pvalue']:.4f}",
        "効果量": f"Cohen's d = {result['cohens_d']:.3f}",
        "推奨": _star("t"),
    },
    {
        "検定手法": "Mann-Whitney U",
        "統計量": f"{result['mw_stat']:.1f}",
        "p値": f"{result['mw_pvalue']:.4f}",
        "効果量": f"r = {result['rank_biserial_r']:.3f}",
        "推奨": _star("mw"),
    },
])
st.dataframe(table_df, hide_index=True, use_container_width=True)

st.subheader("正規性検定（Shapiro-Wilk）")
normality_df = pd.DataFrame([
    {
        "グループ": before_label,
        "n": result["n_before"],
        "平均": f"{result['mean_before']:.4f}",
        "標準偏差": f"{result['std_before']:.4f}",
        "Shapiro-Wilk p値": f"{result['shapiro_before_p']:.4f}",
        "正規性": "✓ 正規" if result["normal_before"] else "✗ 非正規",
    },
    {
        "グループ": after_label,
        "n": result["n_after"],
        "平均": f"{result['mean_after']:.4f}",
        "標準偏差": f"{result['std_after']:.4f}",
        "Shapiro-Wilk p値": f"{result['shapiro_after_p']:.4f}",
        "正規性": "✓ 正規" if result["normal_after"] else "✗ 非正規",
    },
])
st.dataframe(normality_df, hide_index=True, use_container_width=True)

# ── DB 書き込み（失敗してもアプリは継続）────────────────────────
try:
    from _common.db_writer import init_db, write_upload, write_kpi
    init_db()
    uid = write_upload(
        "corrective_action",
        st.session_state.get("uploaded_name"),
        st.session_state.get("row_count"),
    )
    write_kpi(
        uid, "corrective_action",
        datetime.now().strftime("%Y-%m"),
        "p_value", p_val, verdict,
    )
except Exception as _e:
    st.caption(f"⚠ DB書き込みスキップ: {_e}")

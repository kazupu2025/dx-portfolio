"""不良原因自動分類 — テキスト入力 → LLM/ルールベース → カテゴリ分類。"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime
import os
import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import analyze, visualize
from sample_data import generate_sample_csv

st.set_page_config(page_title="不良原因自動分類", page_icon="🏷", layout="wide")
st.markdown("""<style>
[data-testid="stAppViewContainer"]{background-color:#f5f7fa;}
[data-testid="stHeader"]{background-color:#f5f7fa;}
.block-container{padding-top:1rem;}
</style>""", unsafe_allow_html=True)

st.markdown(
    '<div style="background:#1e3a5f;color:white;padding:12px 20px;border-radius:6px;margin-bottom:16px">'
    '<h3 style="margin:0;font-family:BIZ UDGothic">🏷 LLM 不良原因自動分類</h3></div>',
    unsafe_allow_html=True
)

with st.sidebar:
    st.header("⚙ 設定")
    api_key = st.text_input(
        "ANTHROPIC_API_KEY（任意）", type="password",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
        help="未入力の場合はルールベース分類を使用します"
    )
    if api_key:
        os.environ["ANTHROPIC_API_KEY"] = api_key

    st.caption("CSV 列: description（不良説明文）")
    uploaded = st.file_uploader("CSVアップロード", type=["csv"])
    use_sample = st.button("サンプルデータを使用", use_container_width=True)

    if uploaded:
        st.session_state["df"] = pd.read_csv(uploaded)
    elif use_sample:
        st.session_state["df"] = generate_sample_csv()

    df = st.session_state.get("df")
    run_btn = False
    if df is not None:
        run_btn = st.button("▶ 分類実行", type="primary", use_container_width=True)

    st.divider()
    st.subheader("単件テスト")
    single_text = st.text_area("不良説明文を入力", placeholder="例: 外径が0.2mm大きい")
    single_btn = st.button("分類", use_container_width=True)

# 単件テスト処理
if single_btn and single_text:
    from classifier import _rule_classify, _llm_classify
    cat, conf = _rule_classify(single_text)
    if os.environ.get("ANTHROPIC_API_KEY"):
        res = _llm_classify([single_text])
        if res:
            cat, conf = res[0]
    st.sidebar.success(f"カテゴリ: **{cat}**\n確信度: {conf:.0%}")

# メインパネル処理
df = st.session_state.get("df")
if df is None:
    st.info("サイドバーから CSV をアップロードするか、「サンプルデータを使用」をクリックしてください。")
    st.stop()

if run_btn:
    with st.spinner("分類中..."):
        try:
            result = analyze.run_analysis(df)
            st.session_state.update({
                "result": result,
                "uploaded_name": uploaded.name if uploaded else "sample_defect_text.csv",
                "row_count": len(df)
            })
        except ValueError as e:
            st.error(str(e))
            st.stop()

    # DB書き込み試行
    try:
        from _common.db_writer import init_db, write_upload, write_kpi
        init_db()
        uid = write_upload(
            "defect_classifier",
            st.session_state.get("uploaded_name"),
            st.session_state.get("row_count")
        )
        write_kpi(
            uid, "defect_classifier", datetime.now().strftime("%Y-%m"),
            "n_items", float(st.session_state["result"]["n_items"]),
            st.session_state["result"]["verdict"]
        )
    except Exception as _e:
        st.caption(f"⚠ DB書き込みスキップ: {_e}")

result = st.session_state.get("result")
if not result:
    st.info("「▶ 分類実行」を押してください。")
    st.stop()

ni = result["n_items"]
top = result["top_category"]
lu = result["llm_used"]
vd = result["verdict"]
_C = {"good": "#16a34a", "warning": "#d97706"}
_L = {"good": "LLM分類済", "warning": "ルールベース"}
vc, vl = _C[vd], _L[vd]

c1, c2, c3, c4 = st.columns(4)
c1.metric("分類済み件数", f"{ni}件")
c2.metric("最多カテゴリ", top)
c3.metric("カテゴリ数", len(result["category_counts"]))
c4.markdown(
    f'<div style="background:{vc}22;border-left:4px solid {vc};padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{vc};font-size:16px">{vl}</b><br>'
    f'<span style="font-size:12px;color:#64748b">{"APIキーあり" if lu else "APIキーなし（フォールバック）"}</span></div>',
    unsafe_allow_html=True
)

col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(visualize.category_pie_chart(result["category_counts"]), use_container_width=True)
with col_r:
    st.plotly_chart(visualize.category_bar_chart(result["category_counts"]), use_container_width=True)

st.subheader("分類結果詳細")
st.dataframe(result["result_df"], use_container_width=True)

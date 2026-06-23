import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
from analyze import analyze

st.set_page_config(page_title="C-105 リアルタイムSPC監視", layout="wide")
st.title("🔴 リアルタイムSPC監視")

# セッション初期化
if "data" not in st.session_state:
    st.session_state["data"] = []
if "running" not in st.session_state:
    st.session_state["running"] = False
if "sg_counter" not in st.session_state:
    st.session_state["sg_counter"] = 0

# サイドバー設定
with st.sidebar:
    st.header("設定")
    target = st.number_input("目標値", value=50.0)
    sigma = st.number_input("標準偏差", value=1.0, min_value=0.1)
    subgroup_size = st.selectbox("サブグループサイズ", [3, 4, 5], index=2)
    refresh_interval = st.slider("更新間隔(秒)", 0.5, 3.0, 1.0, 0.5)

    col1, col2, col3 = st.columns(3)
    if col1.button("▶ 開始", use_container_width=True):
        st.session_state["running"] = True
    if col2.button("⏹ 停止", use_container_width=True):
        st.session_state["running"] = False
    if col3.button("🔄 リセット", use_container_width=True):
        st.session_state["data"] = []
        st.session_state["sg_counter"] = 0
        st.session_state["running"] = False

    # 異常注入
    st.subheader("テスト用異常注入")
    inject = st.button("⚡ 異常値を注入", use_container_width=True)

# 新データ生成
if st.session_state["running"]:
    rng = np.random.default_rng()
    shift = 5.0 if inject else 0.0
    for _ in range(subgroup_size):
        st.session_state["data"].append({
            "subgroup_id": st.session_state["sg_counter"],
            "value": target + shift + rng.normal(0, sigma)
        })
    st.session_state["sg_counter"] += 1
    # 最新50サブグループのみ保持
    max_rows = 50 * subgroup_size
    if len(st.session_state["data"]) > max_rows:
        st.session_state["data"] = st.session_state["data"][-max_rows:]

# 描画
if len(st.session_state["data"]) >= subgroup_size * 3:
    df = pd.DataFrame(st.session_state["data"])
    result = analyze(df, subgroup_size)
    sg_df = result["sg_df"]

    # KPIカード
    col1, col2, col3, col4 = st.columns(4)
    verdict_color = {"good": "green", "warning": "orange", "alert": "red"}[result["verdict"]]
    col1.metric("X̄ (平均)", f"{result['xbar_bar']:.3f}")
    col2.metric("R̄ (範囲)", f"{result['r_bar']:.3f}")
    col3.metric("逸脱点数", result["n_violations"])
    col4.markdown(f"**判定**: :{verdict_color}[{'✅ 管理内' if result['verdict']=='good' else '⚠️ 要確認' if result['verdict']=='warning' else '🚨 管理外'}]")

    # X-bar管理図
    fig = go.Figure()
    colors = ["red" if sg_df.iloc[i]["subgroup_id"] in result["violations"] else "royalblue"
              for i in range(len(sg_df))]
    fig.add_trace(go.Scatter(x=sg_df["subgroup_id"], y=sg_df["xbar"], mode="lines+markers",
                             marker=dict(color=colors, size=8), name="X̄"))
    fig.add_hline(y=result["ucl_x"], line_dash="dash", line_color="red", annotation_text="UCL")
    fig.add_hline(y=result["xbar_bar"], line_dash="dot", line_color="green", annotation_text="CL")
    fig.add_hline(y=result["lcl_x"], line_dash="dash", line_color="red", annotation_text="LCL")
    fig.update_layout(title="X̄ 管理図", xaxis_title="サブグループ", yaxis_title="平均値", height=300)
    st.plotly_chart(fig, use_container_width=True)

    # R管理図
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=sg_df["subgroup_id"], y=sg_df["r"], name="R", marker_color="steelblue"))
    fig2.add_hline(y=result["ucl_r"], line_dash="dash", line_color="red", annotation_text="UCL(R)")
    fig2.update_layout(title="R 管理図", xaxis_title="サブグループ", yaxis_title="範囲", height=250)
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("「▶ 開始」ボタンを押して監視を開始してください。データが蓄積されるとグラフが表示されます。")

if st.session_state["running"]:
    time.sleep(refresh_interval)
    st.rerun()

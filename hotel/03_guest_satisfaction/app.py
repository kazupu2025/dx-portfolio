# -*- coding: utf-8 -*-
import os
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_PATH = os.path.join(DATA_DIR, "sample_guest_satisfaction.csv")
JSON_PATH = os.path.join(OUTPUT_DIR, "result_analysis.json")

st.set_page_config(page_title="顧客満足度・リピート分析ダッシュボード", layout="wide")
st.title("顧客満足度・リピート分析ダッシュボード")

@st.cache_data
def load_data():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["stay_date"] = pd.to_datetime(df["stay_date"])
    return df

@st.cache_data
def load_result():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

df = load_data()
result = load_result()

# Sidebar filters
st.sidebar.header("フィルタ")
room_types = ["すべて"] + sorted(df["room_type"].unique().tolist())
selected_room = st.sidebar.selectbox("客室タイプ", room_types)

channels = ["すべて"] + sorted(df["channel"].unique().tolist())
selected_channel = st.sidebar.selectbox("予約チャネル", channels)

repeat_options = ["すべて", "リピーター", "新規ゲスト"]
selected_repeat = st.sidebar.selectbox("ゲスト区分", repeat_options)

# Apply filters
filtered = df.copy()
if selected_room != "すべて":
    filtered = filtered[filtered["room_type"] == selected_room]
if selected_channel != "すべて":
    filtered = filtered[filtered["channel"] == selected_channel]
if selected_repeat == "リピーター":
    filtered = filtered[filtered["is_repeat"] == True]
elif selected_repeat == "新規ゲスト":
    filtered = filtered[filtered["is_repeat"] == False]

# ========== Tab 1: KPI サマリー ==========
tab1, tab2, tab3, tab4 = st.tabs(["KPIサマリー", "スコア分析", "チャネル別分析", "明細データ"])

with tab1:
    st.subheader("KPI カード")
    col1, col2, col3, col4 = st.columns(4)

    avg_overall = filtered["overall_score"].mean()
    repeat_rate = (filtered["is_repeat"].sum() / len(filtered)) * 100 if len(filtered) > 0 else 0
    avg_spend = filtered["total_spend"].mean()
    judgment = "good" if avg_overall >= 4.0 else ("warning" if avg_overall >= 3.5 else "alert")

    col1.metric("平均総合スコア", f"{avg_overall:.2f}", delta="/ 5.0")
    col2.metric("リピート率", f"{repeat_rate:.1f}%", delta=None)
    col3.metric("1泊平均支払額", f"¥{avg_spend:,.0f}", delta=None)
    col4.metric("総合判定", judgment.upper(), delta=None)

# ========== Tab 2: スコア分析 ==========
with tab2:
    st.subheader("スコア別詳細分析")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**スコア平均値**")
        score_data = {
            "総合": filtered["overall_score"].mean(),
            "客室": filtered["room_score"].mean(),
            "食事": filtered["food_score"].mean(),
            "サービス": filtered["service_score"].mean(),
        }
        score_df = pd.DataFrame(list(score_data.items()), columns=["項目", "スコア"])
        fig = go.Figure(data=[go.Bar(x=score_df["項目"], y=score_df["スコア"], marker_color="lightblue")])
        fig.add_hline(y=4.0, line_dash="dash", line_color="green", annotation_text="Good")
        fig.add_hline(y=3.5, line_dash="dash", line_color="orange", annotation_text="Warning")
        fig.update_yaxes(range=[0, 5])
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.write("**レーダーチャート（スコア比較）**")
        radar_data = {
            "客室": filtered["room_score"].mean(),
            "食事": filtered["food_score"].mean(),
            "サービス": filtered["service_score"].mean(),
        }
        fig = go.Figure(data=go.Scatterpolar(
            r=list(radar_data.values()),
            theta=list(radar_data.keys()),
            fill='toself'
        ))
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.write("**リピーター vs 新規ゲスト満足度比較**")
    repeat_guests = filtered[filtered["is_repeat"] == True]
    new_guests = filtered[filtered["is_repeat"] == False]

    comparison_data = {
        "区分": ["リピーター", "新規ゲスト"],
        "平均総合スコア": [
            repeat_guests["overall_score"].mean() if len(repeat_guests) > 0 else 0,
            new_guests["overall_score"].mean() if len(new_guests) > 0 else 0,
        ],
        "ゲスト数": [len(repeat_guests), len(new_guests)]
    }
    comparison_df = pd.DataFrame(comparison_data)
    fig = px.bar(comparison_df, x="区分", y="平均総合スコア", hover_data=["ゲスト数"],
                 title="リピーター満足度比較")
    fig.update_yaxes(range=[0, 5])
    st.plotly_chart(fig, use_container_width=True)

# ========== Tab 3: チャネル別分析 ==========
with tab3:
    st.subheader("チャネル別満足度・構成分析")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**チャネル別平均スコア**")
        channel_scores = filtered.groupby("channel").agg({
            "overall_score": "mean",
            "is_repeat": lambda x: (x.sum() / len(x))
        }).reset_index()
        channel_scores.columns = ["チャネル", "平均スコア", "リピート率"]
        fig = px.bar(channel_scores, x="チャネル", y="平均スコア",
                     title="チャネル別平均満足度")
        fig.update_yaxes(range=[0, 5])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.write("**チャネル別予約構成（円グラフ）**")
        channel_counts = filtered["channel"].value_counts().reset_index()
        channel_counts.columns = ["チャネル", "予約数"]
        fig = px.pie(channel_counts, names="チャネル", values="予約数",
                     title="チャネル別予約構成")
        st.plotly_chart(fig, use_container_width=True)

# ========== Tab 4: 明細データ ==========
with tab4:
    st.subheader("明細データ")
    st.info(f"表示件数: {len(filtered)} 件 / 総件数: {len(df)} 件")

    display_cols = ["stay_date", "guest_id", "room_type", "nights", "total_spend",
                    "overall_score", "room_score", "food_score", "service_score",
                    "is_repeat", "channel"]

    st.dataframe(filtered[display_cols].reset_index(drop=True), use_container_width=True)

    csv_data = filtered.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button("CSVダウンロード", data=csv_data,
                       file_name="filtered_guest_satisfaction.csv", mime="text/csv")

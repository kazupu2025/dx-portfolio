# -*- coding: utf-8 -*-
"""
B-61: ホテル 顧客満足度・リピート分析ダッシュボード
Streamlit ダッシュボード
"""
import streamlit as st
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "sample_guest_satisfaction.csv"


@st.cache_data
def load_hotel_guest_satisfaction_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    if "stay_date" in df.columns:
        df["stay_date"] = pd.to_datetime(df["stay_date"], errors="coerce")
    return df


st.title("⭐ B-61 ホテル 顧客満足度・リピート分析ダッシュボード")

df = load_hotel_guest_satisfaction_data()

if df.empty:
    st.error("データファイルが見つかりません。data/sample_guest_satisfaction.csv を確認してください。")
    st.stop()

# サイドバー
with st.sidebar:
    st.header("フィルタ")
    room_types = ["すべて"] + (sorted(df["room_type"].dropna().unique().tolist()) if "room_type" in df.columns else [])
    selected_room = st.selectbox("客室タイプ", room_types)

    channels = ["すべて"] + (sorted(df["channel"].dropna().unique().tolist()) if "channel" in df.columns else [])
    selected_channel = st.selectbox("予約チャネル", channels)

    repeat_options = ["すべて", "リピーター", "新規ゲスト"]
    selected_repeat = st.selectbox("ゲスト区分", repeat_options)

# フィルター適用
filtered = df.copy()
if selected_room != "すべて" and "room_type" in filtered.columns:
    filtered = filtered[filtered["room_type"] == selected_room]
if selected_channel != "すべて" and "channel" in filtered.columns:
    filtered = filtered[filtered["channel"] == selected_channel]
if selected_repeat == "リピーター" and "is_repeat" in filtered.columns:
    filtered = filtered[filtered["is_repeat"] == True]
elif selected_repeat == "新規ゲスト" and "is_repeat" in filtered.columns:
    filtered = filtered[filtered["is_repeat"] == False]

if filtered.empty:
    st.warning("フィルター条件に合致するデータがありません。")
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs(["KPIサマリー", "スコア分析", "チャネル別分析", "明細データ"])

with tab1:
    st.subheader("KPI カード")
    col1, col2, col3, col4 = st.columns(4)

    avg_overall = filtered["overall_score"].mean() if "overall_score" in filtered.columns else 0
    repeat_rate = (filtered["is_repeat"].sum() / len(filtered)) * 100 if "is_repeat" in filtered.columns and len(filtered) > 0 else 0
    avg_spend = filtered["total_spend"].mean() if "total_spend" in filtered.columns else 0
    judgment = "good" if avg_overall >= 4.0 else ("warning" if avg_overall >= 3.5 else "alert")

    col1.metric("平均総合スコア", f"{avg_overall:.2f}", delta="/ 5.0")
    col2.metric("リピート率", f"{repeat_rate:.1f}%")
    col3.metric("1泊平均支払額", f"¥{avg_spend:,.0f}")
    col4.metric("総合判定", judgment.upper())

with tab2:
    st.subheader("スコア別詳細分析")

    score_cols = {
        "総合": "overall_score", "客室": "room_score",
        "食事": "food_score", "サービス": "service_score"
    }
    _avail_scores = {k: v for k, v in score_cols.items() if v in filtered.columns}
    if _avail_scores:
        score_data = {k: filtered[v].mean() for k, v in _avail_scores.items()}
        score_df = pd.DataFrame(list(score_data.items()), columns=["項目", "スコア"])
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**スコア平均値**")
            st.bar_chart(score_df.set_index("項目")["スコア"])
        with col2:
            st.markdown("**スコア一覧**")
            st.dataframe(score_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("**リピーター vs 新規ゲスト満足度比較**")
    if "is_repeat" in filtered.columns and "overall_score" in filtered.columns:
        repeat_guests = filtered[filtered["is_repeat"] == True]
        new_guests = filtered[filtered["is_repeat"] == False]
        comparison_df = pd.DataFrame({
            "区分": ["リピーター", "新規ゲスト"],
            "平均総合スコア": [
                repeat_guests["overall_score"].mean() if len(repeat_guests) > 0 else 0,
                new_guests["overall_score"].mean() if len(new_guests) > 0 else 0,
            ],
        })
        st.bar_chart(comparison_df.set_index("区分")["平均総合スコア"])
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("チャネル別満足度・構成分析")
    if "channel" in filtered.columns and "overall_score" in filtered.columns:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**チャネル別平均スコア**")
            channel_scores = filtered.groupby("channel")["overall_score"].mean().sort_values(ascending=False)
            st.bar_chart(channel_scores)
        with col2:
            st.markdown("**チャネル別予約件数**")
            channel_counts = filtered["channel"].value_counts()
            st.bar_chart(channel_counts)

        if "is_repeat" in filtered.columns:
            st.markdown("**チャネル別リピート率**")
            channel_repeat = filtered.groupby("channel")["is_repeat"].mean() * 100
            st.bar_chart(channel_repeat)

with tab4:
    st.subheader("明細データ")
    st.info(f"表示件数: {len(filtered)} 件 / 総件数: {len(df)} 件")
    display_cols = ["stay_date", "guest_id", "room_type", "nights", "total_spend",
                    "overall_score", "room_score", "food_score", "service_score",
                    "is_repeat", "channel"]
    avail_cols = [c for c in display_cols if c in filtered.columns]
    st.dataframe(filtered[avail_cols].reset_index(drop=True), use_container_width=True)
    csv_data = filtered.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button("CSVダウンロード", data=csv_data,
                       file_name="filtered_guest_satisfaction.csv", mime="text/csv")

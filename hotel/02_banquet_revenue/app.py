# -*- coding: utf-8 -*-
"""
B-60: ホテル 宴会・イベント収益管理ダッシュボード
Streamlit ダッシュボード
"""
import streamlit as st
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ── analyze.py インライン（Streamlit Cloud 互換）──
REQUIRED_COLUMNS = [
    "date", "event_type", "room_name", "guests", "food_revenue",
    "beverage_revenue", "room_fee", "total_revenue", "status"
]


def analyze(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df_comp = df[df["status"] == "完了"]

    total_revenue = float(df_comp["total_revenue"].sum())
    total_events = int(len(df_comp))
    avg_revenue_per_event = float(df_comp["total_revenue"].mean()) if total_events > 0 else 0
    avg_revenue_per_guest = (
        float((df_comp["total_revenue"] / df_comp["guests"].replace(0, 1)).mean())
        if total_events > 0 else 0
    )

    event_df = (
        df_comp.groupby("event_type")
        .agg(count=("date", "count"), total_revenue=("total_revenue", "sum"),
             avg_revenue=("total_revenue", "mean"), avg_guests=("guests", "mean"))
        .reset_index().sort_values("total_revenue", ascending=False)
    )

    room_df = (
        df_comp.groupby("room_name")
        .agg(count=("date", "count"), total_revenue=("total_revenue", "sum"),
             avg_guests=("guests", "mean"))
        .reset_index().sort_values("total_revenue", ascending=False)
    )

    monthly_df = (
        df_comp.groupby(df_comp["date"].dt.to_period("M"))
        .agg(total_revenue=("total_revenue", "sum"), count=("date", "count"))
        .reset_index()
    )
    monthly_df["date"] = monthly_df["date"].astype(str)

    cancel_rate = float((df["status"] == "キャンセル").sum() / len(df) * 100)
    verdict = "good" if avg_revenue_per_guest >= 15000 else ("warning" if avg_revenue_per_guest >= 8000 else "alert")

    return {
        "df": df_comp,
        "event_df": event_df,
        "room_df": room_df,
        "monthly_df": monthly_df,
        "total_revenue": total_revenue,
        "total_events": total_events,
        "avg_revenue_per_event": avg_revenue_per_event,
        "avg_revenue_per_guest": avg_revenue_per_guest,
        "cancel_rate": cancel_rate,
        "verdict": verdict,
    }


@st.cache_data
def load_hotel_banquet_data() -> pd.DataFrame:
    sample_file = BASE_DIR / "sample_banquet.csv"
    if not sample_file.exists():
        return pd.DataFrame()
    return pd.read_csv(sample_file)


st.title("🎊 B-60 ホテル 宴会・イベント収益管理ダッシュボード")
st.markdown("ホテルの宴会・イベント収益分析ダッシュボード")

with st.sidebar:
    st.header("データアップロード")
    uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
else:
    df = load_hotel_banquet_data()

if df.empty:
    st.error("データファイルが見つかりません")
    st.stop()

missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
if missing_cols:
    st.error(f"必須列が不足しています: {', '.join(missing_cols)}")
    st.stop()

result = analyze(df)

# KPI
st.subheader("主要KPI")
col1, col2, col3, col4 = st.columns(4)
col1.metric("総収益", f"¥{result['total_revenue']:,.0f}")
col2.metric("イベント数", f"{result['total_events']}件")
col3.metric("1件平均売上", f"¥{result['avg_revenue_per_event']:,.0f}")
color = "🟢" if result["verdict"] == "good" else "🟡" if result["verdict"] == "warning" else "🔴"
col4.metric("1名単価", f"¥{result['avg_revenue_per_guest']:,.0f}",
            delta=f"{color} {result['verdict'].upper()}")

col_cancel, col_verdict = st.columns(2)
with col_cancel:
    st.info(f"キャンセル率: {result['cancel_rate']:.1f}%")
with col_verdict:
    verdict_text = {"good": "良好 - 高単価を維持", "warning": "注意 - 改善の余地あり", "alert": "警告 - 単価向上が必要"}
    st.warning(verdict_text[result["verdict"]])

st.divider()

# イベント種別分析
st.subheader("イベント種別分析")
event_df = result["event_df"].copy()
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown("**イベント種別別総売上**")
    if "event_type" in event_df.columns and "total_revenue" in event_df.columns:
        st.bar_chart(event_df.set_index("event_type")["total_revenue"])
with col2:
    _e_want = ["event_type", "count", "avg_revenue", "avg_guests"]
    _e_avail = [c for c in _e_want if c in event_df.columns]
    st.dataframe(
        event_df[_e_avail].rename(columns={
            "event_type": "種別", "count": "件数", "avg_revenue": "平均売上", "avg_guests": "平均人数"
        }),
        use_container_width=True,
    )

st.divider()

# 月次トレンド
st.subheader("月次収益トレンド")
monthly_df = result["monthly_df"].copy()
if "date" in monthly_df.columns and "total_revenue" in monthly_df.columns:
    st.line_chart(monthly_df.set_index("date")["total_revenue"])

st.divider()

# 会場別分析
st.subheader("会場別稼働・収益")
room_df = result["room_df"].copy()
_r_want = ["room_name", "count", "total_revenue", "avg_guests"]
_r_avail = [c for c in _r_want if c in room_df.columns]
st.dataframe(
    room_df[_r_avail].rename(columns={
        "room_name": "会場名", "count": "稼働数", "total_revenue": "総売上", "avg_guests": "平均人数"
    }),
    use_container_width=True,
)
if "room_name" in room_df.columns and "total_revenue" in room_df.columns:
    st.markdown("**会場別総売上**")
    st.bar_chart(room_df.set_index("room_name")["total_revenue"])

st.divider()

# 生データ
st.subheader("生データ（完了分）")
_rename = {
    "date": "日付", "event_type": "イベント種別", "room_name": "会場", "guests": "人数",
    "food_revenue": "食事売上", "beverage_revenue": "飲料売上", "room_fee": "会場費",
    "total_revenue": "総売上", "status": "ステータス",
}
st.dataframe(result["df"].rename(columns=_rename), use_container_width=True)

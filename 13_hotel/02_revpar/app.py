# -*- coding: utf-8 -*-
"""
B-59: ホテル RevPAR・客室稼働率ダッシュボード
Streamlit ダッシュボード
"""
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ── analyze.py インライン（Streamlit Cloud 互換）──
REQUIRED_COLUMNS = ["month", "room_type", "total_rooms", "sold_rooms", "adr", "revenue"]


def analyze(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["month"] = pd.to_datetime(df["month"])
    df["occ"] = df["sold_rooms"] / df["total_rooms"] * 100
    df["revpar"] = df["revenue"] / df["total_rooms"]

    monthly_df = df.groupby("month").agg(
        total_rooms=("total_rooms", "sum"),
        sold_rooms=("sold_rooms", "sum"),
        total_revenue=("revenue", "sum"),
    ).reset_index()
    monthly_df["occ"] = monthly_df["sold_rooms"] / monthly_df["total_rooms"] * 100
    monthly_df["revpar"] = monthly_df["total_revenue"] / monthly_df["total_rooms"]
    monthly_df["adr"] = monthly_df["total_revenue"] / monthly_df["sold_rooms"].replace(0, np.nan)

    room_df = df.groupby("room_type").agg(
        avg_occ=("occ", "mean"),
        avg_adr=("adr", "mean"),
        avg_revpar=("revpar", "mean"),
        total_revenue=("revenue", "sum"),
    ).reset_index().sort_values("avg_revpar", ascending=False)

    avg_occ = float(monthly_df["occ"].mean())
    avg_revpar = float(monthly_df["revpar"].mean())
    avg_adr = float(monthly_df["adr"].mean())
    total_revenue = float(df["revenue"].sum())

    verdict = "good" if avg_occ >= 70 else ("warning" if avg_occ >= 55 else "alert")

    return {
        "monthly_df": monthly_df,
        "room_df": room_df,
        "avg_occ": avg_occ,
        "avg_revpar": avg_revpar,
        "avg_adr": avg_adr,
        "total_revenue": total_revenue,
        "verdict": verdict,
    }


st.title("🏨 B-59 ホテル RevPAR・客室稼働率ダッシュボード")

with st.sidebar:
    st.header("データ入力")
    if st.button("📊 サンプルデータを読み込む"):
        sample_path = BASE_DIR / "sample_revpar.csv"
        if sample_path.exists():
            st.session_state["revpar_df"] = pd.read_csv(sample_path)
            st.success("サンプルデータを読み込みました")
        else:
            st.error("sample_revpar.csv が見つかりません")

    uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])
    if uploaded_file is not None:
        try:
            st.session_state["revpar_df"] = pd.read_csv(uploaded_file)
            st.success("ファイルをアップロードしました")
        except Exception as e:
            st.error(f"ファイル読み込みエラー: {e}")

    st.divider()
    if "revpar_df" in st.session_state and st.session_state["revpar_df"] is not None:
        df_side = st.session_state["revpar_df"]
        st.header("フィルタ")
        room_types = df_side["room_type"].unique() if "room_type" in df_side.columns else []
        selected_rooms = st.multiselect("客室タイプを選択", room_types, default=list(room_types))
        st.session_state["revpar_selected_rooms"] = selected_rooms

if "revpar_df" not in st.session_state or st.session_state["revpar_df"] is None:
    st.info("👈 サイドバーからサンプルデータを読み込むか、CSVファイルをアップロードしてください")
else:
    df = st.session_state["revpar_df"]
    selected_rooms = st.session_state.get("revpar_selected_rooms", list(df["room_type"].unique()) if "room_type" in df.columns else [])

    if "room_type" in df.columns and selected_rooms:
        filtered_df = df[df["room_type"].isin(selected_rooms)]
    else:
        filtered_df = df.copy()

    result = analyze(filtered_df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("平均稼働率", f"{result['avg_occ']:.1f}%")
    col2.metric("平均 RevPAR", f"¥{result['avg_revpar']:,.0f}")
    col3.metric("平均 ADR", f"¥{result['avg_adr']:,.0f}")
    verdict_labels = {"good": "✅ 好調", "warning": "⚠️ 注意", "alert": "🔴 警告"}
    col4.metric("判定", verdict_labels.get(result["verdict"], result["verdict"]))

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("月次稼働率 & RevPAR トレンド")
        monthly_data = result["monthly_df"].copy()
        monthly_data["month"] = monthly_data["month"].dt.strftime("%Y-%m")
        chart_data = monthly_data[["month", "occ", "revpar"]].copy()
        chart_data.columns = ["月", "稼働率 (%)", "RevPAR (¥)"]
        st.line_chart(chart_data.set_index("月"))

    with col2:
        st.subheader("客室タイプ別 RevPAR ランキング")
        room_data = result["room_df"].copy().sort_values("avg_revpar", ascending=True)
        st.bar_chart(room_data.set_index("room_type")["avg_revpar"])

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("月次収益構成（客室タイプ別）")
        monthly_by_type = df.groupby(["month", "room_type"])["revenue"].sum().reset_index()
        monthly_by_type["month"] = pd.to_datetime(monthly_by_type["month"]).dt.strftime("%Y-%m")
        pivot_data = monthly_by_type.pivot(index="month", columns="room_type", values="revenue")
        st.bar_chart(pivot_data)

    with col2:
        st.subheader("客室タイプ別 統計")
        _want = ["room_type", "avg_occ", "avg_adr", "avg_revpar", "total_revenue"]
        _avail = [c for c in _want if c in result["room_df"].columns]
        st.dataframe(
            result["room_df"][_avail].rename(columns={
                "room_type": "客室タイプ", "avg_occ": "平均稼働率 (%)",
                "avg_adr": "平均 ADR (¥)", "avg_revpar": "平均 RevPAR (¥)",
                "total_revenue": "総収益 (¥)",
            }),
            hide_index=True, use_container_width=True,
        )

    st.divider()
    st.subheader("月次詳細データ")
    _m_want = ["month", "total_rooms", "sold_rooms", "occ", "adr", "revpar", "total_revenue"]
    _m_avail = [c for c in _m_want if c in result["monthly_df"].columns]
    _disp = result["monthly_df"][_m_avail].copy()
    if "month" in _disp.columns:
        _disp["month"] = pd.to_datetime(_disp["month"]).dt.strftime("%Y-%m")
    st.dataframe(_disp.rename(columns={
        "month": "月", "total_rooms": "総客室数", "sold_rooms": "販売客室数",
        "occ": "稼働率 (%)", "adr": "ADR (¥)", "revpar": "RevPAR (¥)", "total_revenue": "月次収益 (¥)",
    }), hide_index=True, use_container_width=True)

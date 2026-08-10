import streamlit as st
import pandas as pd
import numpy as np
# ── analyze.py インライン（Streamlit Cloud 互換）──
import pandas as pd
import numpy as np

REQUIRED_COLUMNS = ["month", "room_type", "total_rooms", "sold_rooms", "adr", "revenue"]


def analyze(df: pd.DataFrame) -> dict:
    """
    Analyze RevPAR and occupancy data.

    Args:
        df: DataFrame with columns [month, room_type, total_rooms, sold_rooms, adr, revenue]

    Returns:
        Dictionary containing:
        - monthly_df: Monthly aggregated data
        - room_df: Room type analysis sorted by RevPAR
        - avg_occ: Average occupancy rate (%)
        - avg_revpar: Average RevPAR
        - avg_adr: Average ADR
        - total_revenue: Total revenue
        - verdict: Health status (good/warning/alert)
    """
    df = df.copy()
    df["month"] = pd.to_datetime(df["month"])

    # Calculate occupancy and RevPAR
    df["occ"] = df["sold_rooms"] / df["total_rooms"] * 100
    df["revpar"] = df["revenue"] / df["total_rooms"]

    # Monthly aggregation
    monthly_df = df.groupby("month").agg(
        total_rooms=("total_rooms", "sum"),
        sold_rooms=("sold_rooms", "sum"),
        total_revenue=("revenue", "sum"),
    ).reset_index()
    monthly_df["occ"] = monthly_df["sold_rooms"] / monthly_df["total_rooms"] * 100
    monthly_df["revpar"] = monthly_df["total_revenue"] / monthly_df["total_rooms"]
    monthly_df["adr"] = monthly_df["total_revenue"] / monthly_df["sold_rooms"].replace(0, np.nan)

    # Room type analysis
    room_df = df.groupby("room_type").agg(
        avg_occ=("occ", "mean"),
        avg_adr=("adr", "mean"),
        avg_revpar=("revpar", "mean"),
        total_revenue=("revenue", "sum"),
    ).reset_index().sort_values("avg_revpar", ascending=False)

    # Calculate KPIs
    avg_occ = float(monthly_df["occ"].mean())
    avg_revpar = float(monthly_df["revpar"].mean())
    avg_adr = float(monthly_df["adr"].mean())
    total_revenue = float(df["revenue"].sum())

    # Verdict based on occupancy
    if avg_occ >= 70:
        verdict = "good"
    elif avg_occ >= 55:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "monthly_df": monthly_df,
        "room_df": room_df,
        "avg_occ": avg_occ,
        "avg_revpar": avg_revpar,
        "avg_adr": avg_adr,
        "total_revenue": total_revenue,
        "verdict": verdict,
    }

# ────────────────────────────────────────────────
from pathlib import Path

st.title("ホテル RevPAR・客室稼働率ダッシュボード")

# Sidebar
with st.sidebar:
    st.header("データ入力")

    # Sample data button
    if st.button("📊 サンプルデータを読み込む"):
        sample_path = Path(__file__).parent / "sample_revpar.csv"
        if sample_path.exists():
            st.session_state.df = pd.read_csv(sample_path)
            st.success("サンプルデータを読み込みました")

    # CSV upload
    uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])
    if uploaded_file is not None:
        try:
            st.session_state.df = pd.read_csv(uploaded_file)
            st.success("ファイルをアップロードしました")
        except Exception as e:
            st.error(f"ファイル読み込みエラー: {e}")

    st.divider()

    # Room type filter
    if "df" in st.session_state and st.session_state.df is not None:
        st.header("フィルタ")
        room_types = st.session_state.df["room_type"].unique()
        selected_rooms = st.multiselect(
            "客室タイプを選択",
            room_types,
            default=list(room_types),
        )
        st.session_state.selected_rooms = selected_rooms

# Main content
if "df" not in st.session_state or st.session_state.df is None:
    st.info("👈 サイドバーからサンプルデータを読み込むか、CSVファイルをアップロードしてください")
else:
    df = st.session_state.df
    selected_rooms = st.session_state.get("selected_rooms", df["room_type"].unique())

    # Filter data
    filtered_df = df[df["room_type"].isin(selected_rooms)]

    # Analyze
    result = analyze(filtered_df)

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "平均稼働率",
            f"{result['avg_occ']:.1f}%",
            delta=None,
        )

    with col2:
        st.metric(
            "平均 RevPAR",
            f"¥{result['avg_revpar']:,.0f}",
            delta=None,
        )

    with col3:
        st.metric(
            "平均 ADR",
            f"¥{result['avg_adr']:,.0f}",
            delta=None,
        )

    with col4:
        verdict_labels = {"good": "✅ 好調", "warning": "⚠️ 注意", "alert": "🔴 警告"}
        st.metric(
            "判定",
            verdict_labels.get(result["verdict"], result["verdict"]),
            delta=None,
        )

    st.divider()

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("月次稼働率 & RevPAR トレンド")
        monthly_data = result["monthly_df"].copy()
        monthly_data["month"] = monthly_data["month"].dt.strftime("%Y-%m")

        chart_data = monthly_data[["month", "occ", "revpar"]].copy()
        chart_data.columns = ["月", "稼働率 (%)", "RevPAR (¥)"]
        chart_data = chart_data.set_index("月")

        st.line_chart(chart_data)

    with col2:
        st.subheader("客室タイプ別 RevPAR ランキング")
        room_data = result["room_df"].copy()
        room_data = room_data.sort_values("avg_revpar", ascending=True)

        st.bar_chart(room_data.set_index("room_type")["avg_revpar"])

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("月次収益構成（客室タイプ別）")
        monthly_by_type = df.groupby(["month", "room_type"])["revenue"].sum().reset_index()
        monthly_by_type["month"] = pd.to_datetime(monthly_by_type["month"])
        monthly_by_type = monthly_by_type.sort_values("month")
        monthly_by_type["month"] = monthly_by_type["month"].dt.strftime("%Y-%m")

        pivot_data = monthly_by_type.pivot(index="month", columns="room_type", values="revenue")
        st.bar_chart(pivot_data)

    with col2:
        st.subheader("客室タイプ別 統計")
        st.dataframe(
            result["room_df"][["room_type", "avg_occ", "avg_adr", "avg_revpar", "total_revenue"]]
            .rename(columns={
                "room_type": "客室タイプ",
                "avg_occ": "平均稼働率 (%)",
                "avg_adr": "平均 ADR (¥)",
                "avg_revpar": "平均 RevPAR (¥)",
                "total_revenue": "総収益 (¥)",
            }),
            hide_index=True,
            use_container_width=True,
        )

    st.divider()

    st.subheader("詳細データ")
    st.dataframe(
        result["monthly_df"][["month", "total_rooms", "sold_rooms", "occ", "adr", "revpar", "total_revenue"]]
        .rename(columns={
            "month": "月",
            "total_rooms": "総客室数",
            "sold_rooms": "販売客室数",
            "occ": "稼働率 (%)",
            "adr": "ADR (¥)",
            "revpar": "RevPAR (¥)",
            "total_revenue": "月次収益 (¥)",
        })
        .assign(月=lambda x: pd.to_datetime(x["月"]).dt.strftime("%Y-%m")),
        hide_index=True,
        use_container_width=True,
    )

"""
B-29 物流 配送ルート効率化ダッシュボード（Streamlit）
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
CLEANED_CSV = OUTPUT_DIR / "cleaned_route_202401.csv"
REPORT_MD = OUTPUT_DIR / "analysis_report.md"


@st.cache_data
def load_route_efficiency_data() -> pd.DataFrame:
    """B-29専用ローダー（キャッシュキー衝突防止）"""
    if not CLEANED_CSV.exists():
        return pd.DataFrame()
    df = pd.read_csv(CLEANED_CSV, encoding="utf-8-sig")
    for col in ["distance_km", "duration_min", "fuel_cost", "delivery_count",
                "cost_per_km", "cost_per_delivery", "km_per_delivery"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["delay_flag"] = pd.to_numeric(df["delay_flag"], errors="coerce").fillna(0).astype(int)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


st.title("🚚 B-29 物流 配送ルート効率化ダッシュボード")
st.caption("B-29 | 2024年1月 | ルート別コスト・エリア別遅延率・距離vs燃料費分析")

df_all = load_route_efficiency_data()

if df_all.empty:
    st.error("データが見つかりません。先にパイプラインを実行してください。")
    st.stop()

# サイドバー: エリアフィルター
with st.sidebar:
    st.header("🔍 フィルター")
    all_areas = sorted(df_all["area"].dropna().unique().tolist())
    selected_areas = st.multiselect("エリアを選択", options=all_areas, default=all_areas)

df = df_all[df_all["area"].isin(selected_areas)].copy() if selected_areas else df_all.copy()

# KPI 4つ
total_deliveries = int(df["delivery_count"].sum())
avg_delay_rate = df["delay_flag"].mean()
avg_cost_per_delivery = df["cost_per_delivery"].mean()
total_fuel = df["fuel_cost"].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("総配送件数", f"{total_deliveries:,} 件")
col2.metric("平均遅延率", f"{avg_delay_rate:.1%}")
col3.metric("平均1件コスト", f"{avg_cost_per_delivery:,.0f} 円")
col4.metric("総燃料費", f"{total_fuel:,.0f} 円")

st.divider()

# 3タブ
tab1, tab2, tab3 = st.tabs(["📊 ルート別効率", "⚠️ エリア別遅延", "🔵 距離-コスト散布図"])

with tab1:
    st.subheader("ルート別 1件当たりコスト")
    route_avg = (
        df.groupby("route_id")["cost_per_delivery"]
        .mean()
        .reset_index()
        .rename(columns={"cost_per_delivery": "avg_cost_per_delivery"})
        .sort_values("avg_cost_per_delivery")
    )
    median_cpd = route_avg["avg_cost_per_delivery"].median()
    route_avg["効率"] = route_avg["avg_cost_per_delivery"].apply(
        lambda x: "高効率" if x < median_cpd else "低効率"
    )
    fig1 = px.bar(
        route_avg,
        x="avg_cost_per_delivery",
        y="route_id",
        orientation="h",
        color="効率",
        color_discrete_map={"高効率": "#2196F3", "低効率": "#F44336"},
        labels={"avg_cost_per_delivery": "1件当たりコスト（円）", "route_id": "ルートID"},
    )
    fig1.add_vline(x=median_cpd, line_dash="dash", line_color="orange",
                   annotation_text=f"中央値: {median_cpd:.0f}円")
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    st.subheader("エリア別遅延率")
    area_stats = df.groupby("area").agg(
        delay_count=("delay_flag", "sum"),
        run_count=("date", "count"),
    ).reset_index()
    area_stats["delay_rate"] = area_stats["delay_count"] / area_stats["run_count"]
    area_stats["遅延率(%)"] = (area_stats["delay_rate"] * 100).round(1)
    area_stats = area_stats.sort_values("遅延率(%)", ascending=False)
    overall_delay_pct = df["delay_flag"].mean() * 100
    fig2 = px.bar(
        area_stats,
        x="area",
        y="遅延率(%)",
        color="遅延率(%)",
        color_continuous_scale="RdYlGn_r",
        labels={"area": "エリア"},
    )
    fig2.add_hline(y=overall_delay_pct, line_dash="dash", line_color="steelblue",
                   annotation_text=f"全体平均: {overall_delay_pct:.1f}%")
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.subheader("走行距離 vs 燃料費（車両タイプ別）")
    scatter_df = df.dropna(subset=["distance_km", "fuel_cost"])
    fig3 = px.scatter(
        scatter_df,
        x="distance_km",
        y="fuel_cost",
        color="vehicle_type",
        hover_data=["route_id", "area", "delivery_count"],
        labels={
            "distance_km": "走行距離（km）",
            "fuel_cost": "燃料費（円）",
            "vehicle_type": "車両タイプ",
        },
        trendline="ols",
        trendline_scope="overall",
        opacity=0.7,
    )
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# 低効率ルート明細テーブル
st.subheader("🚨 低効率ルート明細（コスト中央値超）")
median_cpd_all = df["cost_per_delivery"].median()
low_eff = df[df["cost_per_delivery"] > median_cpd_all].copy()
low_eff_display = (
    low_eff.groupby("route_id").agg(
        運行回数=("date", "count"),
        平均1件コスト=("cost_per_delivery", "mean"),
        遅延率=("delay_flag", "mean"),
        総配送件数=("delivery_count", "sum"),
    )
    .reset_index()
    .rename(columns={"route_id": "ルートID"})
    .sort_values("平均1件コスト", ascending=False)
)
low_eff_display["平均1件コスト"] = low_eff_display["平均1件コスト"].round(0)
low_eff_display["遅延率"] = low_eff_display["遅延率"].map("{:.1%}".format)
st.dataframe(low_eff_display, use_container_width=True, hide_index=True)

st.divider()

# 分析レポート expander
with st.expander("📄 分析レポートを表示", expanded=False):
    if REPORT_MD.exists():
        st.markdown(REPORT_MD.read_text(encoding="utf-8"))
    else:
        st.warning("分析レポートが見つかりません。analyze.py を実行してください。")

"""
C-17 配送コスト分析パイプライン
Streamlit ダッシュボード
"""
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CSV_PATH = OUTPUT_DIR / "cleaned_delivery_202401.csv"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"

st.set_page_config(
    page_title="配送コスト分析ダッシュボード",
    page_icon="🚚",
    layout="wide",
)

st.title("🚚 物流 配送コスト分析ダッシュボード")
st.caption("C-17 配送コスト分析パイプライン — 2024年1月データ")


@st.cache_data
def load_data():
    if not CSV_PATH.exists():
        return None
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


df = load_data()

if df is None:
    st.error("データが見つかりません。パイプラインを実行してください。")
    st.code("python cleanse.py && python analyze.py && python visualize.py")
    st.stop()

# ─── サイドバー: フィルター ──────────────────────────
with st.sidebar:
    st.header("フィルター")
    all_routes = sorted(df["route_id"].dropna().unique().tolist())
    selected_routes = st.multiselect(
        "ルート選択",
        options=all_routes,
        default=all_routes,
        help="表示するルートを選択してください",
    )
    all_vehicles = sorted(df["vehicle_type"].dropna().unique().tolist())
    selected_vehicles = st.multiselect(
        "車種選択",
        options=all_vehicles,
        default=all_vehicles,
    )

# フィルタリング
if selected_routes and selected_vehicles:
    filtered = df[df["route_id"].isin(selected_routes) & df["vehicle_type"].isin(selected_vehicles)]
else:
    filtered = df.copy()

# ─── メトリクス ─────────────────────────────────────
st.subheader("主要指標")
col1, col2, col3, col4 = st.columns(4)

total_deliveries = int(filtered["delivery_count"].sum()) if "delivery_count" in filtered.columns else 0
total_cost = int(filtered["total_cost"].sum()) if "total_cost" in filtered.columns else 0
avg_cpk = filtered["cost_per_km"].mean() if "cost_per_km" in filtered.columns else 0
delay_rate = (filtered["status"] == "遅延").mean() if "status" in filtered.columns else 0

col1.metric("総配送件数", f"{total_deliveries:,}件")
col2.metric("月間総コスト", f"¥{total_cost:,}")
col3.metric("平均 cost_per_km", f"¥{avg_cpk:.2f}/km")
col4.metric("遅延率", f"{delay_rate:.1%}")

st.divider()

# ─── グラフ ─────────────────────────────────────────
col_l, col_r = st.columns(2)

with col_l:
    st.subheader("ルート別コスト効率")
    chart_route = CHARTS_DIR / "bar_route_cost_per_km.png"
    if chart_route.exists():
        st.image(str(chart_route), use_column_width=True)
    else:
        route_avg = filtered.groupby("route_id")["cost_per_km"].mean().sort_values()
        st.bar_chart(route_avg)

with col_r:
    st.subheader("コスト構成比")
    chart_pie = CHARTS_DIR / "pie_cost_components.png"
    if chart_pie.exists():
        st.image(str(chart_pie), use_column_width=True)
    else:
        cost_cols = ["fuel_cost", "toll_cost", "driver_cost"]
        cost_totals = filtered[cost_cols].sum()
        st.bar_chart(cost_totals)

st.subheader("車種別コスト内訳")
chart_vehicle = CHARTS_DIR / "bar_vehicle_cost_breakdown.png"
if chart_vehicle.exists():
    st.image(str(chart_vehicle), use_column_width=True)
else:
    vehicle_avg = filtered.groupby("vehicle_type")[["fuel_cost", "toll_cost", "driver_cost"]].mean()
    st.bar_chart(vehicle_avg)

st.divider()

# ─── データテーブル ──────────────────────────────────
with st.expander("詳細データ表示", expanded=False):
    st.dataframe(
        filtered.head(200),
        use_container_width=True,
        height=400,
    )

# ─── レポート ────────────────────────────────────────
st.subheader("分析レポート")
if REPORT_PATH.exists():
    report_text = REPORT_PATH.read_text(encoding="utf-8")
    st.markdown(report_text)
else:
    st.warning("レポートが見つかりません。analyze.py を実行してください。")

import streamlit as st
import pandas as pd
import numpy as np
import yaml
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(
    page_title="🌾 農業 農薬・肥料コスト分析",
    page_icon="🌾",
    layout="wide",
)

BASE = Path(__file__).parent

# Load configuration
with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

COST_GOOD = config.get("cost_per_ha_good", 50000)
COST_WARNING = config.get("cost_per_ha_warning", 80000)


@st.cache_data
def load_sample_data():
    """Load sample agri cost data."""
    return pd.read_csv(BASE / "sample_agri_cost.csv", encoding="utf-8")


@st.cache_data
def load_data_from_file(file):
    """Load data from uploaded CSV file."""
    return pd.read_csv(file, encoding="utf-8")


def analyze_data(df):
    """
    Analyze pesticide and fertilizer cost data and compute KPIs.

    Returns dict with aggregated metrics and trend data.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["cost_per_ha"] = df["total_cost"] / df["field_area_ha"]

    # Category-level aggregation
    category_df = (
        df.groupby("category")
        .agg(
            total_cost=("total_cost", "sum"),
            count=("product_name", "count"),
            avg_unit_price=("unit_price", "mean"),
        )
        .reset_index()
        .sort_values("total_cost", ascending=False)
    )

    # Crop-level aggregation
    crop_df = (
        df.groupby("crop")
        .agg(
            total_cost=("total_cost", "sum"),
            avg_cost_per_ha=("cost_per_ha", "mean"),
            category_count=("category", "nunique"),
            field_area_ha=("field_area_ha", "mean"),
        )
        .reset_index()
        .sort_values("avg_cost_per_ha", ascending=False)
    )

    # Monthly trends
    monthly_df = (
        df.groupby("date")
        .agg(
            total_cost=("total_cost", "sum"),
            avg_cost_per_ha=("cost_per_ha", "mean"),
        )
        .reset_index()
    )

    total_cost = float(df["total_cost"].sum())
    cost_per_ha = float(df["cost_per_ha"].mean())
    category_count = int(df["category"].nunique())

    # Verdict
    if cost_per_ha <= COST_GOOD:
        verdict = "good"
    elif cost_per_ha <= COST_WARNING:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "df": df,
        "category_df": category_df,
        "crop_df": crop_df,
        "monthly_df": monthly_df,
        "total_cost": total_cost,
        "cost_per_ha": cost_per_ha,
        "category_count": category_count,
        "verdict": verdict,
    }


# ========== Main UI ==========
st.title("🌾 農業 農薬・肥料コスト分析")
st.caption("12ヶ月のコスト分析 | 4品目（トマト, キャベツ, ほうれん草, じゃがいも）")

# Sidebar: Data loading
st.sidebar.header("📊 データ読み込み")
data_source = st.sidebar.radio("データ源の選択", ["サンプルデータ", "CSVアップロード"])

if data_source == "サンプルデータ":
    df = load_sample_data()
    st.sidebar.success("✓ サンプルデータを読み込みました")
else:
    uploaded_file = st.sidebar.file_uploader("CSVファイルをアップロード", type="csv")
    if uploaded_file:
        df = load_data_from_file(uploaded_file)
        st.sidebar.success("✓ ファイルを読み込みました")
    else:
        df = load_sample_data()
        st.sidebar.info("ファイルが選択されていないため、サンプルデータを使用します")

# Sidebar: Crop filter
crops = sorted(df["crop"].dropna().unique().tolist())
selected_crops = st.sidebar.multiselect("品目フィルター", crops, default=crops)
df_filtered = df[df["crop"].isin(selected_crops)] if selected_crops else df

# Analyze filtered data
result = analyze_data(df_filtered)
category_df = result["category_df"]
crop_df = result["crop_df"]
monthly_df = result["monthly_df"]

# ========== KPI Cards ==========
st.subheader("📈 KPI Summary")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("総コスト (円)", f"{result['total_cost']:,.0f}")

with col2:
    verdict_color = "green" if result["verdict"] == "good" else "orange" if result["verdict"] == "warning" else "red"
    st.metric(
        "ha当たりコスト (円)",
        f"{result['cost_per_ha']:,.0f}",
        delta=f"状態: {result['verdict'].upper()}",
    )

with col3:
    st.metric("利用カテゴリ数", result["category_count"])

with col4:
    verdict_emoji = "✓" if result["verdict"] == "good" else "⚠" if result["verdict"] == "warning" else "✗"
    st.metric("コスト判定", f"{verdict_emoji} {result['verdict'].upper()}")

# ========== Category Cost Pie Chart ==========
st.subheader("📊 カテゴリ別コスト構成")
if len(category_df) > 0:
    fig_category_pie = px.pie(
        category_df,
        values="total_cost",
        names="category",
        title="カテゴリ別コスト (円)",
    )
    fig_category_pie.update_layout(height=400)
    st.plotly_chart(fig_category_pie, use_container_width=True)

# ========== Crop Cost Bar Chart ==========
st.subheader("🌾 作物別コスト")
if len(crop_df) > 0:
    fig_crop_cost = px.bar(
        crop_df,
        x="crop",
        y="total_cost",
        color="total_cost",
        color_continuous_scale="Viridis",
        title="作物別 総コスト",
        labels={"total_cost": "総コスト (円)", "crop": "作物"},
    )
    fig_crop_cost.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_crop_cost, use_container_width=True)

# ========== Cost per HA by Crop ==========
st.subheader("📌 作物別 ha当たりコスト")
if len(crop_df) > 0:
    fig_cost_per_ha = px.bar(
        crop_df,
        x="crop",
        y="avg_cost_per_ha",
        color="avg_cost_per_ha",
        color_continuous_scale="RdYlGn_r",
        title="作物別 平均ha当たりコスト",
        labels={"avg_cost_per_ha": "ha当たりコスト (円)", "crop": "作物"},
    )
    fig_cost_per_ha.add_hline(
        y=COST_GOOD,
        line_dash="dash",
        line_color="green",
        annotation_text=f"Good (≤{COST_GOOD:,.0f}円)",
        annotation_position="right",
    )
    fig_cost_per_ha.add_hline(
        y=COST_WARNING,
        line_dash="dash",
        line_color="orange",
        annotation_text=f"Warning (≤{COST_WARNING:,.0f}円)",
        annotation_position="right",
    )
    fig_cost_per_ha.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_cost_per_ha, use_container_width=True)

# ========== Monthly Cost Trend ==========
st.subheader("📅 月次コスト推移")
if len(monthly_df) > 0:
    fig_monthly_cost = px.line(
        monthly_df,
        x="date",
        y="total_cost",
        markers=True,
        title="月次総コスト",
        labels={"total_cost": "月次コスト (円)", "date": "月"},
    )
    fig_monthly_cost.update_layout(hovermode="x unified", height=400)
    st.plotly_chart(fig_monthly_cost, use_container_width=True)

# ========== Monthly Cost per HA Trend ==========
st.subheader("📈 月次 ha当たりコスト推移")
if len(monthly_df) > 0:
    fig_monthly_cost_per_ha = px.line(
        monthly_df,
        x="date",
        y="avg_cost_per_ha",
        markers=True,
        title="月次平均ha当たりコスト",
        labels={"avg_cost_per_ha": "ha当たりコスト (円)", "date": "月"},
        color_discrete_sequence=["#EF553B"],
    )
    fig_monthly_cost_per_ha.add_hline(
        y=COST_GOOD,
        line_dash="dash",
        line_color="green",
        annotation_text=f"Good: {COST_GOOD:,.0f}円",
        annotation_position="right",
    )
    fig_monthly_cost_per_ha.add_hline(
        y=COST_WARNING,
        line_dash="dash",
        line_color="orange",
        annotation_text=f"Warning: {COST_WARNING:,.0f}円",
        annotation_position="right",
    )
    fig_monthly_cost_per_ha.update_layout(hovermode="x unified", height=400, showlegend=False)
    st.plotly_chart(fig_monthly_cost_per_ha, use_container_width=True)

# ========== Data Table ==========
st.subheader("📋 作物別詳細データ")
st.dataframe(
    crop_df.rename(
        columns={
            "crop": "作物",
            "total_cost": "総コスト (円)",
            "avg_cost_per_ha": "ha当たりコスト (円)",
            "category_count": "利用カテゴリ数",
            "field_area_ha": "平均作付面積 (ha)",
        }
    ),
    use_container_width=True,
)

# ========== Category Detail Table ==========
st.subheader("📋 カテゴリ別詳細データ")
st.dataframe(
    category_df.rename(
        columns={
            "category": "カテゴリ",
            "total_cost": "総コスト (円)",
            "count": "使用回数",
            "avg_unit_price": "平均単価 (円/kg)",
        }
    ),
    use_container_width=True,
)

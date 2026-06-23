import streamlit as st
import pandas as pd
import numpy as np
import yaml
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(
    page_title="🌾 農業 収穫量・品質トレンド",
    page_icon="🌾",
    layout="wide",
)

BASE = Path(__file__).parent

# Load configuration
with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

GRADE_A_GOOD = config.get("grade_a_threshold_good", 75)
GRADE_A_WARNING = config.get("grade_a_threshold_warning", 60)


@st.cache_data
def load_sample_data():
    """Load sample harvest data."""
    return pd.read_csv(BASE / "sample_harvest_quality.csv", encoding="utf-8")


@st.cache_data
def load_data_from_file(file):
    """Load data from uploaded CSV file."""
    return pd.read_csv(file, encoding="utf-8")


def analyze_data(df):
    """
    Analyze harvest data and compute KPIs.

    Returns dict with aggregated metrics and trend data.
    """
    df = df.copy()
    df["month"] = pd.to_datetime(df["month"])
    df["yield_per_ha"] = df["yield_kg"] / df["field_area_ha"]

    # Crop-level aggregation
    crop_df = (
        df.groupby("crop")
        .agg(
            total_yield=("yield_kg", "sum"),
            avg_yield_per_ha=("yield_per_ha", "mean"),
            avg_grade_a=("grade_a_rate", "mean"),
            avg_brix=("avg_brix", "mean"),
            area=("field_area_ha", "mean"),
        )
        .reset_index()
        .sort_values("avg_yield_per_ha", ascending=False)
    )

    # Monthly trends
    monthly_df = (
        df.groupby("month")
        .agg(
            total_yield=("yield_kg", "sum"),
            avg_grade_a=("grade_a_rate", "mean"),
            avg_brix=("avg_brix", "mean"),
        )
        .reset_index()
    )

    # Crop-month detail (for further analysis)
    crop_month_df = (
        df.groupby(["month", "crop"])
        .agg(
            yield_kg=("yield_kg", "sum"),
            avg_grade_a=("grade_a_rate", "mean"),
        )
        .reset_index()
    )

    total_yield = float(df["yield_kg"].sum())
    avg_grade_a = float(df["grade_a_rate"].mean())
    avg_brix = float(df["avg_brix"].mean())

    # Verdict
    if avg_grade_a >= GRADE_A_GOOD:
        verdict = "good"
    elif avg_grade_a >= GRADE_A_WARNING:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "df": df,
        "crop_df": crop_df,
        "monthly_df": monthly_df,
        "crop_month_df": crop_month_df,
        "total_yield": total_yield,
        "avg_grade_a": avg_grade_a,
        "avg_brix": avg_brix,
        "verdict": verdict,
    }


# ========== Main UI ==========
st.title("🌾 農業 収穫量・品質トレンド分析")
st.caption("12ヶ月のデータ分析 | 4品目（トマト, キャベツ, ほうれん草, じゃがいも）")

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
crop_df = result["crop_df"]
monthly_df = result["monthly_df"]
crop_month_df = result["crop_month_df"]

# ========== KPI Cards ==========
st.subheader("📈 KPI Summary")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("総収穫量 (kg)", f"{result['total_yield']:,.0f}")

with col2:
    grade_color = "green" if result["verdict"] == "good" else "orange" if result["verdict"] == "warning" else "red"
    st.metric(
        "A品率 (%)",
        f"{result['avg_grade_a']:.1f}%",
        delta=f"状態: {result['verdict'].upper()}",
    )

with col3:
    st.metric("平均糖度 (Brix)", f"{result['avg_brix']:.1f}")

with col4:
    verdict_emoji = "✓" if result["verdict"] == "good" else "⚠" if result["verdict"] == "warning" else "✗"
    st.metric("品質判定", f"{verdict_emoji} {result['verdict'].upper()}")

# ========== Monthly Trend ==========
st.subheader("📅 月次收穫量トレンド")
if len(crop_month_df) > 0:
    fig_monthly_yield = px.line(
        crop_month_df,
        x="month",
        y="yield_kg",
        color="crop",
        markers=True,
        title="品目別月次収穫量",
        labels={"yield_kg": "収穫量 (kg)", "month": "月", "crop": "品目"},
    )
    fig_monthly_yield.update_layout(hovermode="x unified", height=400)
    st.plotly_chart(fig_monthly_yield, use_container_width=True)

# ========== Grade A Rate by Crop ==========
st.subheader("📊 品目別 A品率")
if len(crop_df) > 0:
    fig_grade_a = px.bar(
        crop_df,
        x="crop",
        y="avg_grade_a",
        color="avg_grade_a",
        color_continuous_scale="RdYlGn",
        title="品目別 平均A品率",
        labels={"avg_grade_a": "A品率 (%)", "crop": "品目"},
    )
    fig_grade_a.add_hline(
        y=GRADE_A_GOOD,
        line_dash="dash",
        line_color="green",
        annotation_text=f"Good (≥{GRADE_A_GOOD}%)",
        annotation_position="right",
    )
    fig_grade_a.add_hline(
        y=GRADE_A_WARNING,
        line_dash="dash",
        line_color="orange",
        annotation_text=f"Warning (≥{GRADE_A_WARNING}%)",
        annotation_position="right",
    )
    fig_grade_a.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_grade_a, use_container_width=True)

# ========== Yield vs Grade A (Scatter) ==========
st.subheader("🎯 収穫量 × A品率 散布図")
if len(crop_df) > 0:
    fig_scatter = px.scatter(
        crop_df,
        x="avg_yield_per_ha",
        y="avg_grade_a",
        size="area",
        color="crop",
        hover_data=["total_yield", "avg_brix"],
        title="単位面積当たり収穫量 vs A品率 (バブルサイズ=作付面積)",
        labels={
            "avg_yield_per_ha": "単位面積当たり収穫量 (kg/ha)",
            "avg_grade_a": "A品率 (%)",
            "crop": "品目",
        },
    )
    fig_scatter.update_layout(height=400)
    st.plotly_chart(fig_scatter, use_container_width=True)

# ========== Grade Distribution (Stacked Bar) ==========
st.subheader("📦 等級構成 (A/B/C品)")
if len(result["df"]) > 0:
    # Aggregate by crop
    grade_dist = (
        result["df"]
        .groupby("crop")[["grade_a_rate", "grade_b_rate", "grade_c_rate"]]
        .mean()
        .reset_index()
        .rename(
            columns={
                "grade_a_rate": "A品",
                "grade_b_rate": "B品",
                "grade_c_rate": "C品",
            }
        )
    )

    fig_grade_dist = go.Figure()
    for grade_type in ["A品", "B品", "C品"]:
        fig_grade_dist.add_trace(
            go.Bar(
                name=grade_type,
                x=grade_dist["crop"],
                y=grade_dist[grade_type],
            )
        )
    fig_grade_dist.update_layout(
        barmode="stack",
        title="品目別 等級構成（積み上げ）",
        xaxis_title="品目",
        yaxis_title="比率 (%)",
        height=400,
    )
    st.plotly_chart(fig_grade_dist, use_container_width=True)

# ========== Data Table ==========
st.subheader("📋 詳細データ")
st.dataframe(
    crop_df.rename(
        columns={
            "crop": "品目",
            "total_yield": "総収穫量 (kg)",
            "avg_yield_per_ha": "単位面積当たり収穫量 (kg/ha)",
            "avg_grade_a": "A品率 (%)",
            "avg_brix": "平均糖度 (Brix)",
            "area": "平均作付面積 (ha)",
        }
    ),
    use_container_width=True,
)

import streamlit as st
import pandas as pd
import yaml
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px

from analyze import analyze, REQUIRED_COLUMNS

st.set_page_config(
    page_title="🌾 農業 出荷先別単価・販売分析",
    page_icon="🌾",
    layout="wide",
)

BASE = Path(__file__).parent

# Load configuration
with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

DIRECT_SALES_GOOD = config.get("direct_sales_good", 0.30)
DIRECT_SALES_WARNING = config.get("direct_sales_warning", 0.15)


@st.cache_data
def load_sample_data():
    """Load sample sales channel data."""
    return pd.read_csv(BASE / "sample_sales_channel.csv", encoding="utf-8")


@st.cache_data
def load_data_from_file(file):
    """Load data from uploaded CSV file."""
    return pd.read_csv(file, encoding="utf-8")


def validate_columns(df):
    """Validate that all required columns are present."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        st.error(f"❌ 必須列がありません: {', '.join(missing)}")
        return False
    return True


st.title("🌾 農業 出荷先別単価・販売分析")
st.markdown(
    "チャネル別売上・単価集計、作物×チャネル分析、直販比率による高単価チャネル活用度の評価"
)

# Sidebar: File upload or sample data
st.sidebar.header("📁 データ入力")
use_sample = st.sidebar.checkbox("サンプルデータを使用する", value=True)

if use_sample:
    df = load_sample_data()
    st.sidebar.success("✓ サンプルデータを読み込みました")
else:
    uploaded_file = st.sidebar.file_uploader(
        "CSVファイルをアップロード",
        type="csv"
    )
    if uploaded_file:
        df = load_data_from_file(uploaded_file)
        st.sidebar.success(f"✓ {uploaded_file.name} を読み込みました")
    else:
        df = None

if df is not None:
    if not validate_columns(df):
        st.stop()

    # Analyze data
    results = analyze(df, config)

    # KPI Cards
    st.header("📊 KPI")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "🏆 総売上",
            f"¥{results['total_revenue']:,.0f}",
        )

    with col2:
        st.metric(
            "💹 平均単価",
            f"¥{results['avg_unit_price']:.0f}/kg",
        )

    with col3:
        st.metric(
            "📈 直販比率",
            f"{results['direct_sales_ratio']:.1%}",
        )

    with col4:
        verdict = results["verdict"]
        if verdict == "good":
            verdict_icon = "✅"
            verdict_color = "green"
        elif verdict == "warning":
            verdict_icon = "⚠️"
            verdict_color = "orange"
        else:
            verdict_icon = "❌"
            verdict_color = "red"
        st.metric("判定", f"{verdict_icon} {verdict.upper()}")

    # Verdict explanation
    st.markdown("---")
    if results["direct_sales_ratio"] >= DIRECT_SALES_GOOD:
        st.success(
            f"✅ 直販比率が {DIRECT_SALES_GOOD:.0%} 以上です。"
            "高単価チャネル（直販）をうまく活用できています。"
        )
    elif results["direct_sales_ratio"] >= DIRECT_SALES_WARNING:
        st.warning(
            f"⚠️ 直販比率が {DIRECT_SALES_WARNING:.0%}～{DIRECT_SALES_GOOD:.0%} です。"
            "直販比率をさらに高めることで売上改善が期待できます。"
        )
    else:
        st.error(
            f"❌ 直販比率が {DIRECT_SALES_WARNING:.0%} 未満です。"
            "直販チャネルの強化を検討してください。"
        )

    # Visualizations
    st.header("📈 分析グラフ")

    # 1. Channel sales composition (pie chart)
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("チャネル別売上構成")
        fig_channel = px.pie(
            results["channel_df"],
            values="total_revenue",
            names="channel",
            title="",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_channel.update_layout(
            height=400,
            showlegend=True,
            font=dict(size=12),
        )
        st.plotly_chart(fig_channel, use_container_width=True)

    # 2. Channel average unit price (bar chart, sorted high to low)
    with col2:
        st.subheader("チャネル別平均単価（高→低順）")
        channel_price = results["channel_df"].sort_values(
            "avg_unit_price", ascending=False
        )
        fig_price = px.bar(
            channel_price,
            x="channel",
            y="avg_unit_price",
            title="",
            labels={"channel": "出荷先", "avg_unit_price": "平均単価（円/kg）"},
            color="avg_unit_price",
            color_continuous_scale="RdYlGn",
        )
        fig_price.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_price, use_container_width=True)

    # 3. Monthly sales trend by channel
    st.subheader("月次売上トレンド（チャネル別）")
    monthly_channel = (
        results["df"]
        .groupby(["month", "channel"])
        .agg(total_revenue=("revenue", "sum"))
        .reset_index()
    )
    fig_monthly = px.line(
        monthly_channel,
        x="month",
        y="total_revenue",
        color="channel",
        title="",
        labels={"month": "月", "total_revenue": "売上（円）"},
        markers=True,
    )
    fig_monthly.update_layout(height=400)
    st.plotly_chart(fig_monthly, use_container_width=True)

    # 4. Channel x Crop cross-tabulation
    st.subheader("作物×チャネル クロス集計（売上）")
    pivot_df = results["channel_crop_df"].pivot_table(
        index="crop",
        columns="channel",
        values="total_revenue",
        aggfunc="sum",
    ).fillna(0)
    st.dataframe(pivot_df, use_container_width=True)

    # Detailed tables
    st.header("📋 詳細データ")

    tab1, tab2, tab3 = st.tabs(["チャネル別集計", "作物別集計", "生データ"])

    with tab1:
        st.subheader("チャネル別集計")
        st.dataframe(results["channel_df"], use_container_width=True)

    with tab2:
        st.subheader("作物別集計")
        st.dataframe(results["crop_df"], use_container_width=True)

    with tab3:
        st.subheader("生データ")
        st.dataframe(results["df"], use_container_width=True)

else:
    st.info("📂 左のサイドバーからデータを読み込んでください。")

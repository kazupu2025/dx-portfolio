import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from analyze import analyze

st.set_page_config(
    page_title="C-101 出荷検査合否率・保留件数 週次レポート",
    page_icon="📦",
    layout="wide",
)

BASE = Path(__file__).parent


@st.cache_data
def load_sample():
    """Load sample shipping inspection data."""
    return pd.read_csv(BASE / "sample_shipping_inspection.csv")


st.title("📦 出荷検査合否率・保留件数 週次レポート")
st.caption("C-101 | 製造業向け")

# Sidebar
st.sidebar.header("データ入力")

sample_data = load_sample()

col_upload, col_sample = st.sidebar.columns(2)
with col_upload:
    uploaded_file = st.file_uploader("CSVアップロード", type=["csv"])

with col_sample:
    use_sample = st.button("📥 サンプルデータ使用")

if use_sample:
    st.session_state.df_input = sample_data.copy()

if uploaded_file is not None:
    try:
        df_input = pd.read_csv(uploaded_file)
        st.session_state.df_input = df_input
        st.sidebar.success(f"✅ {len(df_input)}行のデータをロード")
    except Exception as e:
        st.sidebar.error(f"❌ ファイル読み込みエラー: {e}")

if "df_input" not in st.session_state:
    st.info("サイドバーからCSVをアップロードするか、サンプルデータボタンを押してください。")
    st.stop()

df = st.session_state.df_input

try:
    result = analyze(df)
except Exception as e:
    st.error(f"分析エラー: {e}")
    st.stop()

# KPI Cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "合格率",
        f"{result['pass_rate']:.2f}%",
        delta="✅ 正常" if result["verdict"] == "good" else
              "⚠️ 要注視" if result["verdict"] == "warning" else "🚨 要対応",
        delta_color="normal" if result["verdict"] == "good" else "off"
    )

with col2:
    st.metric(
        "保留件数",
        f"{result['hold_count']}件",
        delta="保留ロット数（不合格時）"
    )

with col3:
    st.metric(
        "検査総件数",
        f"{result['total']}件"
    )

with col4:
    verdict_text = {
        "good": "✅ 良好",
        "warning": "⚠️ 警告",
        "alert": "🚨 警報"
    }[result["verdict"]]
    st.metric("判定", verdict_text)

st.divider()

# Weekly Pass Rate Chart
st.subheader("📈 週次合格率の推移")
weekly_df = result["weekly_df"]

if len(weekly_df) > 0:
    fig_weekly = px.line(
        weekly_df,
        x="week",
        y="pass_rate",
        markers=True,
        title="週次合格率",
        labels={"week": "週", "pass_rate": "合格率(%)"},
        color_discrete_sequence=["#0068C9"]
    )
    fig_weekly.add_hline(
        y=95, line_dash="dash", line_color="orange",
        annotation_text="警告ライン (95%)", annotation_position="right"
    )
    fig_weekly.add_hline(
        y=98, line_dash="dash", line_color="red",
        annotation_text="警報ライン (98%)", annotation_position="right"
    )
    fig_weekly.update_layout(height=400, hovermode="x unified")
    st.plotly_chart(fig_weekly, use_container_width=True)
else:
    st.warning("週次データなし")

# Product Pass Rate Chart
st.subheader("🏭 製品別合格率")
product_df = result["product_df"].sort_values("pass_rate", ascending=True)

if len(product_df) > 0:
    fig_product = px.barh(
        product_df,
        x="pass_rate",
        y="product",
        title="製品別合格率",
        labels={"pass_rate": "合格率(%)", "product": "製品"},
        color="pass_rate",
        color_continuous_scale=["#d73027", "#fee090", "#1a9850"]
    )
    fig_product.update_layout(height=300)
    st.plotly_chart(fig_product, use_container_width=True)
else:
    st.warning("製品データなし")

st.divider()

# Weekly Summary Table
st.subheader("📋 週次サマリー")
display_weekly = weekly_df[[
    "week", "total", "passed", "hold", "pass_rate"
]].copy()
display_weekly.columns = ["週", "検査件数", "合格件数", "保留件数", "合格率(%)"]
display_weekly["合格率(%)"] = display_weekly["合格率(%)"].apply(lambda x: f"{x:.2f}%")
st.dataframe(display_weekly, use_container_width=True, hide_index=True)

# Product Summary Table
st.subheader("🏭 製品別サマリー")
display_product = product_df[[
    "product", "total", "passed", "pass_rate"
]].copy()
display_product.columns = ["製品", "検査件数", "合格件数", "合格率(%)"]
display_product["合格率(%)"] = display_product["合格率(%)"].apply(lambda x: f"{x:.2f}%")
display_product = display_product.sort_values("製品")
st.dataframe(display_product, use_container_width=True, hide_index=True)

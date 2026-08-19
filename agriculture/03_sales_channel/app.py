# -*- coding: utf-8 -*-
"""
B-64: 農業 出荷先別単価・販売分析ダッシュボード
Streamlit ダッシュボード
"""
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

try:
    import yaml
    with open(BASE_DIR / "config.yml", encoding="utf-8") as _f:
        _config = yaml.safe_load(_f)
except Exception:
    _config = {}

DIRECT_SALES_GOOD = _config.get("direct_sales_good", 0.30)
DIRECT_SALES_WARNING = _config.get("direct_sales_warning", 0.15)

REQUIRED_COLUMNS = ["month", "crop", "channel", "quantity_kg", "unit_price", "revenue", "grade"]


@st.cache_data
def load_agri_sales_channel_data() -> pd.DataFrame:
    path = BASE_DIR / "sample_sales_channel.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8")


def analyze(df: pd.DataFrame) -> dict:
    df = df.copy()
    if "month" in df.columns:
        df["month"] = pd.to_datetime(df["month"], errors="coerce")

    c_agg = {}
    if "quantity_kg" in df.columns:
        c_agg["total_quantity"] = ("quantity_kg", "sum")
    if "revenue" in df.columns:
        c_agg["total_revenue"] = ("revenue", "sum")
    if "unit_price" in df.columns:
        c_agg["avg_unit_price"] = ("unit_price", "mean")
    channel_df = (
        df.groupby("channel").agg(**c_agg).reset_index().sort_values("total_revenue", ascending=False)
    ) if "channel" in df.columns and c_agg else pd.DataFrame()

    cr_agg = {}
    if "quantity_kg" in df.columns:
        cr_agg["total_quantity"] = ("quantity_kg", "sum")
    if "revenue" in df.columns:
        cr_agg["total_revenue"] = ("revenue", "sum")
    if "unit_price" in df.columns:
        cr_agg["avg_unit_price"] = ("unit_price", "mean")
    crop_df = (
        df.groupby("crop").agg(**cr_agg).reset_index().sort_values("total_revenue", ascending=False)
    ) if "crop" in df.columns and cr_agg else pd.DataFrame()

    m_agg = {}
    if "revenue" in df.columns:
        m_agg["total_revenue"] = ("revenue", "sum")
    if "quantity_kg" in df.columns:
        m_agg["total_quantity"] = ("quantity_kg", "sum")
    if "unit_price" in df.columns:
        m_agg["avg_unit_price"] = ("unit_price", "mean")
    monthly_df = (
        df.groupby("month").agg(**m_agg).reset_index()
    ) if "month" in df.columns and m_agg else pd.DataFrame()

    total_revenue = float(df["revenue"].sum()) if "revenue" in df.columns else 0
    avg_unit_price = float(df["unit_price"].mean()) if "unit_price" in df.columns else 0
    direct_sales_revenue = float(df[df["channel"] == "直販"]["revenue"].sum()) if "channel" in df.columns and "revenue" in df.columns else 0
    direct_sales_ratio = direct_sales_revenue / total_revenue if total_revenue > 0 else 0
    verdict = "good" if direct_sales_ratio >= DIRECT_SALES_GOOD else ("warning" if direct_sales_ratio >= DIRECT_SALES_WARNING else "alert")

    return {
        "df": df, "channel_df": channel_df, "crop_df": crop_df, "monthly_df": monthly_df,
        "total_revenue": total_revenue, "avg_unit_price": avg_unit_price,
        "direct_sales_ratio": direct_sales_ratio, "verdict": verdict,
    }


st.title("🚜 B-64 農業 出荷先別単価・販売分析ダッシュボード")
st.markdown("チャネル別売上・単価集計、直販比率による高単価チャネル活用度の評価")

with st.sidebar:
    st.header("📁 データ入力")
    use_sample = st.checkbox("サンプルデータを使用する", value=True)
    uploaded_file = None
    if not use_sample:
        uploaded_file = st.file_uploader("CSVファイルをアップロード", type="csv")

if use_sample or uploaded_file is None:
    df_raw = load_agri_sales_channel_data()
else:
    try:
        df_raw = pd.read_csv(uploaded_file, encoding="utf-8")
    except Exception:
        df_raw = pd.DataFrame()

if df_raw.empty:
    st.info("📂 サンプルデータが見つかりません。sample_sales_channel.csv を確認してください。")
    st.stop()

missing_cols = [c for c in REQUIRED_COLUMNS if c not in df_raw.columns]
if missing_cols:
    st.error(f"❌ 必須列がありません: {', '.join(missing_cols)}")
    st.stop()

results = analyze(df_raw)

# KPI
st.header("📊 KPI")
col1, col2, col3, col4 = st.columns(4)
col1.metric("🏆 総売上", f"¥{results['total_revenue']:,.0f}")
col2.metric("💹 平均単価", f"¥{results['avg_unit_price']:.0f}/kg")
col3.metric("📈 直販比率", f"{results['direct_sales_ratio']:.1%}")
verdict = results["verdict"]
verdict_icon = "✅" if verdict == "good" else "⚠️" if verdict == "warning" else "❌"
col4.metric("判定", f"{verdict_icon} {verdict.upper()}")

st.markdown("---")
if results["direct_sales_ratio"] >= DIRECT_SALES_GOOD:
    st.success(f"✅ 直販比率が {DIRECT_SALES_GOOD:.0%} 以上です。高単価チャネルをうまく活用できています。")
elif results["direct_sales_ratio"] >= DIRECT_SALES_WARNING:
    st.warning(f"⚠️ 直販比率が {DIRECT_SALES_WARNING:.0%}～{DIRECT_SALES_GOOD:.0%} です。直販比率をさらに高めることで売上改善が期待できます。")
else:
    st.error(f"❌ 直販比率が {DIRECT_SALES_WARNING:.0%} 未満です。直販チャネルの強化を検討してください。")

# グラフ
st.header("📈 分析グラフ")
channel_df = results["channel_df"]
col1, col2 = st.columns(2)
with col1:
    st.subheader("チャネル別売上構成")
    if not channel_df.empty and "channel" in channel_df.columns and "total_revenue" in channel_df.columns:
        st.bar_chart(channel_df.set_index("channel")["total_revenue"])
with col2:
    st.subheader("チャネル別平均単価（高→低）")
    if not channel_df.empty and "channel" in channel_df.columns and "avg_unit_price" in channel_df.columns:
        _ch = channel_df.sort_values("avg_unit_price", ascending=False)
        st.bar_chart(_ch.set_index("channel")["avg_unit_price"])

st.subheader("月次売上トレンド（チャネル別）")
if "channel" in results["df"].columns and "month" in results["df"].columns and "revenue" in results["df"].columns:
    monthly_channel = (
        results["df"].groupby(["month", "channel"])["revenue"].sum().reset_index()
    )
    monthly_channel["month"] = monthly_channel["month"].dt.strftime("%Y-%m") if hasattr(monthly_channel["month"], "dt") else monthly_channel["month"].astype(str)
    pivot_monthly = monthly_channel.pivot(index="month", columns="channel", values="revenue").fillna(0)
    st.line_chart(pivot_monthly)

# 作物×チャネル クロス集計
st.subheader("作物×チャネル クロス集計（売上）")
if "channel" in results["df"].columns and "crop" in results["df"].columns and "revenue" in results["df"].columns:
    pivot_df = results["df"].groupby(["crop", "channel"])["revenue"].sum().unstack(fill_value=0)
    st.dataframe(pivot_df, use_container_width=True)

# 詳細データ
st.header("📋 詳細データ")
tab1, tab2, tab3 = st.tabs(["チャネル別集計", "作物別集計", "生データ"])
with tab1:
    st.dataframe(results["channel_df"], use_container_width=True)
with tab2:
    st.dataframe(results["crop_df"], use_container_width=True)
with tab3:
    st.dataframe(results["df"], use_container_width=True)

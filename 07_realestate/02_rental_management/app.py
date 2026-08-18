"""
B-37 賃貸物件管理・空室率ダッシュボード
"""
import streamlit as st
import pandas as pd
import yaml
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "output"
CSV = OUT / "cleaned_rental_202401.csv"
REPORT = OUT / "analysis_report.md"
CHARTS = OUT / "charts"

st.title("🏠 B-37 賃貸物件管理・空室率レポート")
st.caption("B-37 | 5エリア × 5物件タイプ | 空室率・月次収益・エリア別アラート管理")


@st.cache_data
def load_rental_management_data() -> pd.DataFrame:
    """B-37専用ローダー（キャッシュキー衝突防止）"""
    if not CSV.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV, encoding="utf-8-sig")
    for col in ["rent", "management_fee", "management_cost", "repair_cost",
                "monthly_revenue", "total_cost", "net_income"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if "is_vacant" in df.columns:
        df["is_vacant"] = pd.to_numeric(df["is_vacant"], errors="coerce").fillna(0)
    return df


@st.cache_data
def load_rental_management_cfg() -> dict:
    """B-37 設定ローダー"""
    p = BASE / "config.yml"
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


df = load_rental_management_data()
cfg = load_rental_management_cfg()

if df.empty:
    st.error("cleaned_rental_202401.csv が見つかりません。パイプラインを実行してください。")
    st.code("python run_pipeline.py", language="bash")
    st.stop()

vacancy_threshold = cfg.get("vacancy_alert_threshold", 0.20)

# ---- サイドバー: フィルター ----
with st.sidebar:
    st.header("🔍 フィルター")
    areas = sorted(df["area"].unique())
    selected_areas = st.multiselect("エリア", areas, default=areas)

filtered = df[df["area"].isin(selected_areas)] if selected_areas else df

# ---- KPIメトリクス ----
total_props = len(filtered)
overall_vacancy = filtered["is_vacant"].mean()
total_revenue = filtered["monthly_revenue"].sum()
total_net = filtered["net_income"].sum()

area_grp = filtered.groupby("area").agg(
    total=("property_id", "count"),
    vacant=("is_vacant", "sum"),
).reset_index()
area_grp["vacancy_rate"] = area_grp["vacant"] / area_grp["total"]
alert_count = (area_grp["vacancy_rate"] > vacancy_threshold).sum()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("総物件数", f"{total_props} 件")
col2.metric("空室率", f"{overall_vacancy*100:.1f}%",
            delta=f"{(overall_vacancy - vacancy_threshold)*100:.1f}% vs 閾値",
            delta_color="inverse")
col3.metric("月次総収益", f"¥{total_revenue:,.0f}")
col4.metric("月次純収益", f"¥{total_net:,.0f}")
col5.metric("⚠ 空室アラートエリア数", f"{alert_count} エリア")

st.divider()

# ---- タブ ----
tab1, tab2, tab3 = st.tabs(["エリア別空室率", "タイプ別収益", "エリア別収益"])

with tab1:
    chart_path = CHARTS / "bar_area_vacancy_rate.png"
    if chart_path.exists():
        st.image(str(chart_path), use_container_width=True)
    else:
        st.warning("グラフを生成してください: python output/visualize.py")

    st.subheader("エリア別サマリー（空室率高い順）")
    area_summary = filtered.groupby("area").agg(
        物件数=("property_id", "count"),
        空室数=("is_vacant", "sum"),
        平均賃料=("rent", "mean"),
        月次収益合計=("monthly_revenue", "sum"),
    ).reset_index()
    area_summary["空室率(%)"] = (area_summary["空室数"] / area_summary["物件数"] * 100).round(1)
    area_summary["平均賃料"] = area_summary["平均賃料"].round(0).astype(int)
    area_summary["月次収益合計"] = area_summary["月次収益合計"].astype(int)
    area_summary = area_summary.sort_values("空室率(%)", ascending=False)
    st.dataframe(area_summary, use_container_width=True, hide_index=True)

with tab2:
    chart_path = CHARTS / "bar_type_net_income.png"
    if chart_path.exists():
        st.image(str(chart_path), use_container_width=True)
    else:
        st.warning("グラフを生成してください: python output/visualize.py")

with tab3:
    chart_path = CHARTS / "bar_area_revenue.png"
    if chart_path.exists():
        st.image(str(chart_path), use_container_width=True)
    else:
        st.warning("グラフを生成してください: python output/visualize.py")

st.divider()

with st.expander("分析レポート（詳細）", expanded=False):
    if REPORT.exists():
        st.markdown(REPORT.read_text(encoding="utf-8"))
    else:
        st.warning("analysis_report.md が見つかりません。analyze.py を実行してください。")

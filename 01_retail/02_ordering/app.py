import streamlit as st
import pandas as pd
import yaml
from pathlib import Path

st.set_page_config(
    page_title="小売 発注最適化ダッシュボード",
    page_icon="🛒",
    layout="wide",
)

BASE = Path(__file__).parent

with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

OVERSTOCK_TH = config.get("overstock_days_threshold", 30)
LEAD_TIME    = config.get("lead_time_days", 3)


@st.cache_data
def load_forecast():
    df = pd.read_csv(BASE / "output" / "forecast_202401.csv", encoding="utf-8-sig")
    for col in ["avg_daily_sales", "forecast_31days", "recommended_order",
                "days_of_stock", "current_stock", "safety_stock"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["stockout_risk"] = df["stockout_risk"].astype(bool)
    df["overstock"]     = df["overstock"].astype(bool)
    return df


@st.cache_data
def load_report():
    p = BASE / "output" / "analysis_report.md"
    return p.read_text(encoding="utf-8") if p.exists() else "レポートが見つかりません"


df_all    = load_forecast()
report_md = load_report()

st.title("🛒 小売 発注最適化ダッシュボード")
st.caption("2024年1月需要予測 | 50商品 | 5カテゴリ")

col_f1, col_f2 = st.columns(2)
with col_f1:
    cats = sorted(df_all["category"].unique().tolist())
    sel_cats = st.multiselect("カテゴリフィルター", cats, default=cats)
with col_f2:
    risk_filter = st.selectbox("リスクフィルター", ["全商品", "欠品リスクのみ", "過剰在庫のみ"])

df = df_all[df_all["category"].isin(sel_cats)] if sel_cats else df_all
if risk_filter == "欠品リスクのみ":
    df = df[df["stockout_risk"]]
elif risk_filter == "過剰在庫のみ":
    df = df[df["overstock"]]

total_prods     = len(df)
stockout_count  = int(df["stockout_risk"].sum())
overstock_count = int(df["overstock"].sum())
total_forecast  = df["forecast_31days"].sum()
total_order     = df["recommended_order"].sum()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("対象商品数",         f"{total_prods}品")
c2.metric("⚠ 欠品リスク",      f"{stockout_count}品",
          delta="要緊急発注" if stockout_count > 0 else "問題なし",
          delta_color="inverse" if stockout_count > 0 else "normal")
c3.metric("⚠ 過剰在庫",        f"{overstock_count}品",
          delta="発注停止推奨" if overstock_count > 0 else "問題なし",
          delta_color="inverse" if overstock_count > 0 else "normal")
c4.metric("月次総予測需要",     f"{total_forecast:,.0f}個")
c5.metric("月次総推奨発注量",   f"{total_order:,.0f}個")

st.divider()

tab1, tab2, tab3 = st.tabs(["📊 カテゴリ別予測", "⚠ 欠品リスク", "🔵 在庫日数散布図"])
charts_dir = BASE / "output" / "charts"

with tab1:
    p = charts_dir / "bar_category_forecast.png"
    st.image(str(p), use_container_width=True) if p.exists() else st.warning("グラフなし")

with tab2:
    p = charts_dir / "bar_stockout_risk.png"
    st.image(str(p), use_container_width=True) if p.exists() else st.warning("グラフなし")
    if stockout_count > 0:
        st.caption(f"赤 = 欠品リスク（現在庫 < LT需要+安全在庫）")

with tab3:
    p = charts_dir / "scatter_stock_forecast.png"
    st.image(str(p), use_container_width=True) if p.exists() else st.warning("グラフなし")

st.divider()

st.subheader("推奨発注リスト（発注量多い順）")
order_tbl = df[df["recommended_order"] > 0].sort_values("recommended_order", ascending=False).copy()
order_tbl["欠品リスク"] = order_tbl["stockout_risk"].map({True: "⚠ あり", False: "なし"})
order_tbl["過剰在庫"]   = order_tbl["overstock"].map({True: "⚠ あり", False: "なし"})
disp_cols = ["product_id", "product_name", "category",
             "avg_daily_sales", "current_stock", "forecast_31days", "recommended_order",
             "days_of_stock", "欠品リスク", "過剰在庫"]
disp_cols = [c for c in disp_cols if c in order_tbl.columns]
order_tbl = order_tbl[disp_cols]
order_tbl.columns = ["商品ID", "商品名", "カテゴリ",
                     "日次平均販売", "現在庫", "月次予測需要", "推奨発注量",
                     "在庫日数", "欠品リスク", "過剰在庫"][:len(disp_cols)]
st.dataframe(order_tbl, use_container_width=True)

st.divider()
with st.expander("📋 分析レポートを見る", expanded=False):
    st.markdown(report_md)

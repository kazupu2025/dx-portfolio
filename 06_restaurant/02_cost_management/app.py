import streamlit as st
import pandas as pd
import yaml
from pathlib import Path

st.set_page_config(
    page_title="飲食 原価・食材ロスダッシュボード",
    page_icon="🍽️",
    layout="wide",
)

BASE = Path(__file__).parent

with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)
WASTE_ALERT = config.get("waste_rate_alert_threshold", 0.10)


@st.cache_data
def load_data():
    df = pd.read_csv(BASE / "output" / "cleaned_cost_202401.csv", encoding="utf-8-sig")
    for col in ["purchase_cost", "waste_cost", "waste_rate", "purchase_qty", "waste_qty", "unit_cost", "used_qty"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


@st.cache_data
def load_report():
    p = BASE / "output" / "analysis_report.md"
    return p.read_text(encoding="utf-8") if p.exists() else "レポートが見つかりません"


df_all = load_data()
report_text = load_report()

st.title("🍽️ 飲食 原価・食材ロスダッシュボード")
st.caption("2024年1月 | 5店舗")

stores = sorted(df_all["store"].dropna().unique().tolist())
selected = st.multiselect("店舗フィルター", stores, default=stores)
df = df_all[df_all["store"].isin(selected)] if selected else df_all

total_purchase = df["purchase_cost"].sum()
total_waste    = df["waste_cost"].sum()
overall_loss   = total_waste / total_purchase * 100 if total_purchase > 0 else 0
store_loss     = df.groupby("store").apply(
    lambda g: g["waste_qty"].sum() / g["purchase_qty"].sum() * 100
    if g["purchase_qty"].sum() > 0 else 0
)
alert_stores   = (store_loss > WASTE_ALERT * 100).sum()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("月次総仕入コスト",   f"¥{total_purchase:,.0f}")
c2.metric("月次総廃棄コスト",   f"¥{total_waste:,.0f}",
          delta=f"ロス率 {overall_loss:.2f}%",
          delta_color="inverse" if overall_loss > WASTE_ALERT * 100 else "normal")
c3.metric("全体ロス率",         f"{overall_loss:.2f}%",
          delta="要対応" if overall_loss > WASTE_ALERT * 100 else "正常",
          delta_color="inverse" if overall_loss > WASTE_ALERT * 100 else "normal")
c4.metric("アラート店舗数",     f"{alert_stores}店舗",
          delta="要改善" if alert_stores > 0 else "問題なし",
          delta_color="inverse" if alert_stores > 0 else "normal")
c5.metric("対象店舗数",         f"{df['store'].nunique()}店舗")

st.divider()

tab1, tab2, tab3 = st.tabs(["📦 カテゴリ別仕入", "🏪 店舗別ロス率", "🗑️ 廃棄上位食材"])
charts_dir = BASE / "output" / "charts"

with tab1:
    p = charts_dir / "bar_category_cost.png"
    st.image(str(p), use_container_width=True) if p.exists() else st.warning("グラフなし")

with tab2:
    p = charts_dir / "bar_store_loss_rate.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
        st.caption(f"赤棒 = ロス率{WASTE_ALERT*100:.0f}%超（アラート）")
    else:
        st.warning("グラフなし")

with tab3:
    p = charts_dir / "bar_ingredient_waste.png"
    st.image(str(p), use_container_width=True) if p.exists() else st.warning("グラフなし")

st.divider()

st.subheader("カテゴリ別 ロス率サマリー")
cat_tbl = df.groupby("category").agg(
    仕入コスト合計=("purchase_cost", "sum"),
    廃棄コスト合計=("waste_cost",    "sum"),
).copy()
cat_tbl["ロス率(%)"] = (cat_tbl["廃棄コスト合計"] / cat_tbl["仕入コスト合計"].replace(0, 1) * 100).round(2)
cat_tbl["アラート"] = cat_tbl["ロス率(%)"].apply(
    lambda x: "要対応" if x > WASTE_ALERT * 100 else "正常"
)
cat_tbl = cat_tbl.sort_values("ロス率(%)", ascending=False)
cat_tbl["仕入コスト合計"] = cat_tbl["仕入コスト合計"].apply(lambda x: f"¥{x:,.0f}")
cat_tbl["廃棄コスト合計"] = cat_tbl["廃棄コスト合計"].apply(lambda x: f"¥{x:,.0f}")
st.dataframe(cat_tbl, use_container_width=True)

st.divider()

with st.expander("📋 分析レポートを見る", expanded=False):
    st.markdown(report_text)

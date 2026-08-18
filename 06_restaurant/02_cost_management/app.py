import streamlit as st
import pandas as pd
import yaml
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUTPUT_DIR = BASE / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"

st.title("🍽️ B-35 飲食 原価・食材ロス管理ダッシュボード")
st.caption("B-35 | 2024年1月 | 5店舗 | カテゴリ別仕入コスト・廃棄ロス率・店舗別アラート")


@st.cache_data
def load_restaurant_cost_config() -> dict:
    """B-35 設定ローダー"""
    p = BASE / "config.yml"
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


@st.cache_data
def load_restaurant_cost_data() -> pd.DataFrame:
    """B-35専用ローダー（キャッシュキー衝突防止）"""
    p = OUTPUT_DIR / "cleaned_cost_202401.csv"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p, encoding="utf-8-sig")
    for col in ["purchase_cost", "waste_cost", "waste_rate", "purchase_qty", "waste_qty", "unit_cost", "used_qty"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


@st.cache_data
def load_restaurant_cost_report() -> str:
    """B-35 レポートローダー"""
    p = OUTPUT_DIR / "analysis_report.md"
    return p.read_text(encoding="utf-8") if p.exists() else "レポートが見つかりません"


config = load_restaurant_cost_config()
WASTE_ALERT = config.get("waste_rate_alert_threshold", 0.10)

df_all = load_restaurant_cost_data()
report_text = load_restaurant_cost_report()

if df_all.empty:
    st.error("データが見つかりません。パイプラインを実行してください。")
    st.stop()

# ---- サイドバー: 店舗フィルター ----
with st.sidebar:
    st.header("🔍 フィルター")
    stores = sorted(df_all["store"].dropna().unique().tolist())
    selected = st.multiselect("店舗フィルター", stores, default=stores)

df = df_all[df_all["store"].isin(selected)] if selected else df_all

# ---- KPI ----
total_purchase = df["purchase_cost"].sum()
total_waste    = df["waste_cost"].sum()
overall_loss   = total_waste / total_purchase * 100 if total_purchase > 0 else 0
store_loss     = df.groupby("store").apply(
    lambda g: g["waste_qty"].sum() / g["purchase_qty"].sum() * 100
    if g["purchase_qty"].sum() > 0 else 0
)
alert_stores = (store_loss > WASTE_ALERT * 100).sum()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("月次総仕入コスト", f"¥{total_purchase:,.0f}")
c2.metric("月次総廃棄コスト", f"¥{total_waste:,.0f}",
          delta=f"ロス率 {overall_loss:.2f}%",
          delta_color="inverse" if overall_loss > WASTE_ALERT * 100 else "normal")
c3.metric("全体ロス率", f"{overall_loss:.2f}%",
          delta="要対応" if overall_loss > WASTE_ALERT * 100 else "正常",
          delta_color="inverse" if overall_loss > WASTE_ALERT * 100 else "normal")
c4.metric("アラート店舗数", f"{alert_stores}店舗",
          delta="要改善" if alert_stores > 0 else "問題なし",
          delta_color="inverse" if alert_stores > 0 else "normal")
c5.metric("対象店舗数", f"{df['store'].nunique()}店舗")

st.divider()

tab1, tab2, tab3 = st.tabs(["📦 カテゴリ別仕入", "🏪 店舗別ロス率", "🗑️ 廃棄上位食材"])

with tab1:
    p = CHARTS_DIR / "bar_category_cost.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning("グラフなし。visualize.py を実行してください。")

with tab2:
    p = CHARTS_DIR / "bar_store_loss_rate.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
        st.caption(f"赤棒 = ロス率{WASTE_ALERT*100:.0f}%超（アラート）")
    else:
        st.warning("グラフなし。visualize.py を実行してください。")

with tab3:
    p = CHARTS_DIR / "bar_ingredient_waste.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning("グラフなし。visualize.py を実行してください。")

st.divider()

st.subheader("カテゴリ別 ロス率サマリー")
cat_tbl = df.groupby("category").agg(
    仕入コスト合計=("purchase_cost", "sum"),
    廃棄コスト合計=("waste_cost", "sum"),
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

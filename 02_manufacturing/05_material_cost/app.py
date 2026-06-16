import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="製造 原材料コスト変動ダッシュボード",
    page_icon="🏭",
    layout="wide",
)

BASE = Path(__file__).parent


@st.cache_data
def load_data():
    p = BASE / "output" / "cleaned_material_202401.csv"
    df = pd.read_csv(p, encoding="utf-8-sig")
    for col in ["quantity", "unit_price", "prev_month_price", "price_change_rate", "total_cost"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if "purchase_date" in df.columns:
        df["purchase_date"] = pd.to_datetime(df["purchase_date"], errors="coerce")
    return df


@st.cache_data
def load_report():
    p = BASE / "output" / "analysis_report.md"
    return p.read_text(encoding="utf-8") if p.exists() else "レポートが見つかりません"


df_all = load_data()
report_text = load_report()

st.title("🏭 製造 原材料コスト変動ダッシュボード")
st.caption("2024年1月 | 20原材料 | 5仕入先")

# カテゴリフィルター
categories = sorted(df_all["category"].dropna().unique().tolist()) if "category" in df_all.columns else []
selected_cats = st.multiselect("カテゴリフィルター", categories, default=categories)
df = df_all[df_all["category"].isin(selected_cats)] if selected_cats else df_all

# KPI 4つ
total_cost = df["total_cost"].sum()
n_soar = int((df["price_change_flag"] == "急騰").sum()) if "price_change_flag" in df.columns else 0
n_drop = int((df["price_change_flag"] == "急落").sum()) if "price_change_flag" in df.columns else 0
avg_change = df["price_change_rate"].mean() * 100 if "price_change_rate" in df.columns else 0.0

c1, c2, c3, c4 = st.columns(4)
c1.metric("仕入総額", f"{total_cost:,.0f}")
c2.metric("急騰品目数", f"{n_soar} 件",
          delta="要注意" if n_soar > 0 else "問題なし",
          delta_color="inverse" if n_soar > 0 else "normal")
c3.metric("急落品目数", f"{n_drop} 件",
          delta="機会あり" if n_drop > 0 else "なし",
          delta_color="normal")
c4.metric("平均変動率", f"{avg_change:+.2f}%",
          delta="上昇傾向" if avg_change > 0 else "下落傾向",
          delta_color="inverse" if avg_change > 5 else "normal")

st.divider()

# 3タブ
tab1, tab2, tab3 = st.tabs(["カテゴリ別コスト", "単価変動ランキング", "仕入先構成"])
charts_dir = BASE / "output" / "charts"

with tab1:
    p = charts_dir / "bar_category_cost.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning("グラフが見つかりません。visualize.py を先に実行してください。")

    cat_tbl = df.groupby("category").agg(
        仕入コスト合計=("total_cost", "sum"),
        取引件数=("total_cost", "count"),
    ).copy()
    cat_tbl["仕入コスト合計"] = cat_tbl["仕入コスト合計"].apply(lambda x: f"{x:,.0f}")
    cat_tbl = cat_tbl.sort_values("取引件数", ascending=False)
    st.dataframe(cat_tbl, use_container_width=True)

with tab2:
    p = charts_dir / "bar_material_price_change.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning("グラフが見つかりません。visualize.py を先に実行してください。")

with tab3:
    p = charts_dir / "pie_supplier_cost.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning("グラフが見つかりません。visualize.py を先に実行してください。")

    sup_tbl = df.groupby("supplier").agg(
        仕入コスト合計=("total_cost", "sum"),
        取引件数=("total_cost", "count"),
    ).copy()
    total_sup = sup_tbl["仕入コスト合計"].sum()
    sup_tbl["構成比(%)"] = (sup_tbl["仕入コスト合計"] / total_sup * 100).round(1)
    sup_tbl["仕入コスト合計"] = sup_tbl["仕入コスト合計"].apply(lambda x: f"{x:,.0f}")
    sup_tbl = sup_tbl.sort_values("構成比(%)", ascending=False)
    st.dataframe(sup_tbl, use_container_width=True)

st.divider()

# 急騰・急落明細テーブル
st.subheader("急騰・急落 明細")
if "price_change_flag" in df.columns:
    flag_filter = st.radio("フィルター", ["急騰", "急落", "すべて"], horizontal=True)
    if flag_filter == "すべて":
        alert_df = df[df["price_change_flag"].isin(["急騰", "急落"])].copy()
    else:
        alert_df = df[df["price_change_flag"] == flag_filter].copy()

    if len(alert_df) > 0:
        disp_cols = [c for c in [
            "purchase_date", "material_code", "material_name", "category",
            "supplier", "unit_price", "prev_month_price", "price_change_rate",
            "price_change_flag", "total_cost",
        ] if c in alert_df.columns]
        disp = alert_df[disp_cols].copy()
        if "price_change_rate" in disp.columns:
            disp["price_change_rate"] = (disp["price_change_rate"] * 100).round(2)
        st.dataframe(disp.sort_values("price_change_rate", ascending=False)
                     if "price_change_rate" in disp.columns else disp,
                     use_container_width=True)
    else:
        st.info("該当データなし")
else:
    st.info("price_change_flag 列がありません")

st.divider()

# 分析レポート expander
with st.expander("分析レポートを見る", expanded=False):
    st.markdown(report_text)

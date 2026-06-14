import streamlit as st
import pandas as pd
import yaml
from pathlib import Path

st.set_page_config(
    page_title="物流 在庫・欠品検知ダッシュボード",
    page_icon="📦",
    layout="wide",
)

BASE = Path(__file__).parent

with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

STOCKOUT_THRESHOLD = config.get("stockout_alert_threshold", 0)
LOW_STOCK_RATIO_THRESHOLD = config.get("low_stock_ratio_threshold", 0.20)


@st.cache_data
def load_data():
    df = pd.read_csv(BASE / "output" / "cleaned_inventory_202401.csv", encoding="utf-8-sig")
    for col in ["stock_qty", "min_stock_qty", "unit_cost", "received_qty", "shipped_qty"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["stock_value"] = df["stock_qty"] * df["unit_cost"]
    df["stockout_flag"] = df["stock_qty"] < df["min_stock_qty"]
    return df


@st.cache_data
def load_report():
    p = BASE / "output" / "analysis_report.md"
    return p.read_text(encoding="utf-8") if p.exists() else "レポートが見つかりません"


df_all = load_data()
report_text = load_report()

st.title("📦 物流 在庫・欠品検知ダッシュボード")
st.caption("2024年1月 | 5倉庫")

warehouses = sorted(df_all["warehouse"].dropna().unique().tolist())
selected = st.multiselect("倉庫フィルター", warehouses, default=warehouses)
df = df_all[df_all["warehouse"].isin(selected)] if selected else df_all

total_stock_value = df["stock_value"].sum()
stockout_count = int(df["stockout_flag"].sum())
total_items = len(df)
stockout_ratio = stockout_count / total_items * 100 if total_items > 0 else 0
warehouse_count = df["warehouse"].nunique()
row_count = len(df)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("総在庫金額", f"¥{total_stock_value:,.0f}")
c2.metric("欠品品目数", f"{stockout_count} 件",
          delta="要対応" if stockout_count > 0 else "正常",
          delta_color="inverse" if stockout_count > 0 else "normal")
ratio_delta = f"{'⚠ アラート' if stockout_ratio > LOW_STOCK_RATIO_THRESHOLD * 100 else '正常'}"
c3.metric("欠品率", f"{stockout_ratio:.1f}%", delta=ratio_delta,
          delta_color="inverse" if stockout_ratio > LOW_STOCK_RATIO_THRESHOLD * 100 else "normal")
c4.metric("対象倉庫数", f"{warehouse_count} 倉庫")
c5.metric("レコード数", f"{row_count:,} 件")

st.divider()

tab1, tab2, tab3 = st.tabs(["📊 倉庫別在庫金額", "🔴 倉庫別欠品品目数", "📈 在庫回転率"])
charts_dir = BASE / "output" / "charts"

with tab1:
    p = charts_dir / "bar_warehouse_stock.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning("グラフが見つかりません。run_pipeline.py を実行してください。")

with tab2:
    p = charts_dir / "bar_stockout_items.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
        st.caption("赤棒 = 欠品品目数（stock_qty < min_stock_qty）")
    else:
        st.warning("グラフが見つかりません。run_pipeline.py を実行してください。")

with tab3:
    p = charts_dir / "scatter_turnover.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
        st.caption("赤点 = 欠品品目、青点 = 正常品目")
    else:
        st.warning("グラフが見つかりません。run_pipeline.py を実行してください。")

st.divider()

st.subheader("欠品品目一覧")
stockout_items = df[df["stockout_flag"]].copy()
if len(stockout_items) > 0:
    show_cols = [c for c in ["warehouse", "item_code", "item_name", "category",
                              "stock_qty", "min_stock_qty", "unit_cost"] if c in stockout_items.columns]
    st.dataframe(stockout_items[show_cols].sort_values("warehouse"), use_container_width=True)
else:
    st.success("欠品品目はありません")

st.divider()

st.subheader("倉庫別在庫サマリー")
wh_tbl = df.groupby("warehouse").agg(
    在庫金額合計=("stock_value", "sum"),
    欠品品目数=("stockout_flag", "sum"),
    品目数=("item_code", "nunique"),
).copy()
wh_tbl["欠品率(%)"] = (wh_tbl["欠品品目数"] / df.groupby("warehouse").size() * 100).round(1)
wh_tbl["アラート"] = wh_tbl["欠品品目数"].apply(
    lambda x: "⚠ 要対応" if x > 0 else "✅ 正常"
)
wh_tbl["在庫金額合計"] = wh_tbl["在庫金額合計"].apply(lambda x: f"¥{x:,.0f}")
wh_tbl = wh_tbl.sort_values("欠品品目数", ascending=False)
st.dataframe(wh_tbl, use_container_width=True)

st.divider()

with st.expander("📋 分析レポートを見る", expanded=False):
    st.markdown(report_text)

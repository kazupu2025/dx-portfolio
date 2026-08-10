"""物流 在庫・欠品検知ダッシュボード — Plotly 動的チャート版"""
import streamlit as st
import pandas as pd
import plotly.express as px
import yaml
from pathlib import Path

BASE = Path(__file__).parent
with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)
LOW_STOCK_RATIO = config.get("low_stock_ratio_threshold", 0.20)


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
st.caption("2024年1月 | 5倉庫 | サンプルデータ")

warehouses = sorted(df_all["warehouse"].dropna().unique().tolist())
selected = st.multiselect("倉庫フィルター", warehouses, default=warehouses)
df = df_all[df_all["warehouse"].isin(selected)] if selected else df_all

total_stock_value = df["stock_value"].sum()
stockout_count    = int(df["stockout_flag"].sum())
total_items       = len(df)
stockout_ratio    = stockout_count / total_items * 100 if total_items > 0 else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("総在庫金額", f"¥{total_stock_value:,.0f}")
c2.metric("欠品品目数", f"{stockout_count} 件",
          delta="要対応" if stockout_count > 0 else "正常",
          delta_color="inverse" if stockout_count > 0 else "normal")
c3.metric("欠品率", f"{stockout_ratio:.1f}%",
          delta="⚠ アラート" if stockout_ratio > LOW_STOCK_RATIO * 100 else "正常",
          delta_color="inverse" if stockout_ratio > LOW_STOCK_RATIO * 100 else "normal")
c4.metric("対象倉庫数", f"{df['warehouse'].nunique()} 倉庫")
c5.metric("レコード数", f"{total_items:,} 件")

st.divider()

tab1, tab2, tab3 = st.tabs(["📊 倉庫別在庫金額", "🔴 欠品品目数", "📈 在庫回転率"])

with tab1:
    wh_stock = (
        df.groupby("warehouse")["stock_value"].sum().reset_index()
        .rename(columns={"warehouse": "倉庫", "stock_value": "在庫金額(円)"})
        .sort_values("在庫金額(円)", ascending=False)
    )
    fig = px.bar(wh_stock, x="倉庫", y="在庫金額(円)", title="倉庫別 在庫金額（2024年1月）",
                 text="在庫金額(円)", color_discrete_sequence=["#3b82f6"])
    fig.update_traces(texttemplate="¥%{text:,.0f}", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    wh_stockout = (
        df.groupby("warehouse")["stockout_flag"].sum().reset_index()
        .rename(columns={"warehouse": "倉庫", "stockout_flag": "欠品品目数"})
        .sort_values("欠品品目数", ascending=False)
    )
    wh_stockout["状態"] = wh_stockout["欠品品目数"].apply(
        lambda x: "欠品あり" if x > 0 else "正常"
    )
    fig2 = px.bar(wh_stockout, x="倉庫", y="欠品品目数",
                  color="状態", color_discrete_map={"欠品あり": "#ef4444", "正常": "#3b82f6"},
                  title="倉庫別 欠品品目数（stock_qty < min_stock_qty）", text="欠品品目数")
    fig2.update_traces(textposition="outside")
    fig2.update_layout(showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    if "shipped_qty" in df.columns and "stock_qty" in df.columns:
        item_turn = df.groupby("item_name").agg(
            出荷数=("shipped_qty", "sum"), 在庫数=("stock_qty", "mean"),
            欠品=("stockout_flag", "any"),
        ).reset_index()
        item_turn["回転率"] = (item_turn["出荷数"] / item_turn["在庫数"].replace(0, 1)).round(2)
        fig3 = px.scatter(
            item_turn, x="在庫数", y="出荷数", color="欠品",
            color_discrete_map={True: "#ef4444", False: "#3b82f6"},
            hover_name="item_name", title="在庫数 vs 出荷数（散布図）",
            labels={"欠品": "欠品フラグ"},
        )
        st.plotly_chart(fig3, use_container_width=True)
        st.caption("赤点 = 欠品品目（在庫 < 最低在庫）、青点 = 正常品目")
    else:
        st.info("出荷データがありません")

st.divider()

st.subheader("欠品品目一覧")
stockout_items = df[df["stockout_flag"]].copy()
if len(stockout_items) > 0:
    show_cols = [c for c in ["warehouse", "item_code", "item_name", "category",
                              "stock_qty", "min_stock_qty", "unit_cost"] if c in stockout_items.columns]
    st.dataframe(stockout_items[show_cols].sort_values("warehouse"), use_container_width=True)
else:
    st.success("✅ 欠品品目はありません")

st.divider()

st.subheader("倉庫別在庫サマリー")
wh_tbl = df.groupby("warehouse").agg(
    在庫金額合計=("stock_value", "sum"),
    欠品品目数=("stockout_flag", "sum"),
    品目数=("item_code", "nunique"),
).copy()
wh_tbl["欠品率(%)"] = (wh_tbl["欠品品目数"] / df.groupby("warehouse").size() * 100).round(1)
wh_tbl["アラート"] = wh_tbl["欠品品目数"].apply(lambda x: "⚠ 要対応" if x > 0 else "✅ 正常")
wh_tbl["在庫金額合計"] = wh_tbl["在庫金額合計"].apply(lambda x: f"¥{x:,.0f}")
st.dataframe(wh_tbl.sort_values("欠品品目数", ascending=False), use_container_width=True)

st.divider()
with st.expander("📋 分析レポートを見る", expanded=False):
    st.markdown(report_text)

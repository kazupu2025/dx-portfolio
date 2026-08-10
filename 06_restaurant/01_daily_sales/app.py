"""飲食店 日次売上・廃棄ロス ダッシュボード — Plotly 動的チャート版"""
import streamlit as st
import pandas as pd
import plotly.express as px
import yaml
from pathlib import Path

BASE = Path(__file__).parent
with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)
WASTE_ALERT = config.get("waste_loss_alert_threshold", 0.05)


@st.cache_data
def load_data():
    df = pd.read_csv(BASE / "output" / "cleaned_sales_202401.csv", encoding="utf-8-sig")
    for col in ["sales_amount", "waste_amount", "quantity", "waste_qty"]:
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

st.title("🍽️ 飲食店 日次売上・廃棄ロス ダッシュボード")
st.caption("2024年1月 | 5店舗 | サンプルデータ")

stores = sorted(df_all["store_name"].dropna().unique().tolist())
selected = st.multiselect("店舗フィルター", stores, default=stores)
df = df_all[df_all["store_name"].isin(selected)] if selected else df_all

total_sales = df["sales_amount"].sum()
total_waste = df["waste_amount"].sum()
waste_rate = total_waste / total_sales * 100 if total_sales > 0 else 0
alert_pct = WASTE_ALERT * 100

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("総売上", f"¥{total_sales:,.0f}")
c2.metric("廃棄損失", f"¥{total_waste:,.0f}")
c3.metric("廃棄ロス率", f"{waste_rate:.2f}%",
          delta="⚠ アラート" if waste_rate > alert_pct else "正常",
          delta_color="inverse" if waste_rate > alert_pct else "normal")
c4.metric("対象店舗数", f"{df['store_name'].nunique()} 店")
c5.metric("レコード数", f"{len(df):,} 件")

st.divider()

tab1, tab2, tab3 = st.tabs(["📊 店舗別売上", "📈 日次トレンド", "♻️ 廃棄ロス率"])

with tab1:
    store_sales = (
        df.groupby("store_name")["sales_amount"].sum().reset_index()
        .rename(columns={"store_name": "店舗", "sales_amount": "売上(円)"})
        .sort_values("売上(円)", ascending=False)
    )
    fig = px.bar(store_sales, x="店舗", y="売上(円)", title="店舗別 売上合計（2024年1月）",
                 text="売上(円)", color_discrete_sequence=["#3b82f6"])
    fig.update_traces(texttemplate="¥%{text:,.0f}", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    daily = df.groupby("date")["sales_amount"].sum().reset_index()
    daily.columns = ["日付", "売上(円)"]
    fig2 = px.line(daily, x="日付", y="売上(円)", title="日次 売上トレンド（2024年1月）",
                   markers=True)
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    waste_tbl = df.groupby("store_name").agg(
        売上=("sales_amount", "sum"), 廃棄=("waste_amount", "sum")
    ).reset_index()
    waste_tbl["廃棄ロス率(%)"] = (waste_tbl["廃棄"] / waste_tbl["売上"] * 100).round(2)
    waste_tbl["状態"] = waste_tbl["廃棄ロス率(%)"].apply(
        lambda x: "アラート" if x > alert_pct else "正常"
    )
    fig3 = px.bar(waste_tbl, x="store_name", y="廃棄ロス率(%)",
                  color="状態", color_discrete_map={"アラート": "#ef4444", "正常": "#3b82f6"},
                  title="店舗別 廃棄ロス率（2024年1月）", text="廃棄ロス率(%)")
    fig3.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig3.add_hline(y=alert_pct, line_dash="dash", line_color="orange",
                   annotation_text=f"アラートライン ({alert_pct:.0f}%)", annotation_position="top right")
    fig3.update_layout(showlegend=False, xaxis_title="店舗")
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

st.subheader("店舗別 廃棄ロス集計")
waste_summary = df.groupby("store_name").agg(
    売上合計=("sales_amount", "sum"), 廃棄損失合計=("waste_amount", "sum")
).copy()
waste_summary["廃棄ロス率(%)"] = (waste_summary["廃棄損失合計"] / waste_summary["売上合計"] * 100).round(2)
waste_summary["アラート"] = waste_summary["廃棄ロス率(%)"].apply(
    lambda x: "⚠ アラート" if x > alert_pct else "✅ 正常"
)
waste_summary["売上合計"] = waste_summary["売上合計"].apply(lambda x: f"¥{x:,.0f}")
waste_summary["廃棄損失合計"] = waste_summary["廃棄損失合計"].apply(lambda x: f"¥{x:,.0f}")
st.dataframe(waste_summary.sort_values("廃棄ロス率(%)", ascending=False), use_container_width=True)

st.divider()
with st.expander("📋 分析レポートを見る", expanded=False):
    st.markdown(report_text)

import streamlit as st
import pandas as pd
import yaml
from pathlib import Path

st.set_page_config(
    page_title="飲食店 日次売上・廃棄ロス ダッシュボード",
    page_icon="🍽️",
    layout="wide",
)

BASE = Path(__file__).parent

with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)
WASTE_ALERT_THRESHOLD = config.get("waste_loss_alert_threshold", 0.05)

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
st.caption("2024年1月 | 5店舗")

# ── 店舗フィルター ──────────────────────────────────────
stores = sorted(df_all["store_name"].dropna().unique().tolist())
selected = st.multiselect("店舗フィルター", stores, default=stores)
df = df_all[df_all["store_name"].isin(selected)] if selected else df_all

# ── メトリクスカード ────────────────────────────────────
total_sales = df["sales_amount"].sum()
total_waste = df["waste_amount"].sum()
waste_rate = (total_waste / total_sales * 100) if total_sales > 0 else 0
store_count = df["store_name"].nunique()
row_count = len(df)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("総売上", f"¥{total_sales:,.0f}")
c2.metric("廃棄損失", f"¥{total_waste:,.0f}")
alert_delta = f"{'⚠ アラート' if waste_rate > WASTE_ALERT_THRESHOLD * 100 else '正常'}"
c3.metric("廃棄ロス率", f"{waste_rate:.2f}%", delta=alert_delta,
          delta_color="inverse" if waste_rate > WASTE_ALERT_THRESHOLD * 100 else "normal")
c4.metric("対象店舗数", f"{store_count} 店")
c5.metric("レコード数", f"{row_count:,} 件")

st.divider()

# ── グラフ タブ ─────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 店舗別売上", "📈 日次トレンド", "♻️ 廃棄ロス率"])

charts_dir = BASE / "output" / "charts"

with tab1:
    p = charts_dir / "bar_store_sales.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning("グラフが見つかりません。run_pipeline.py を実行してください。")

with tab2:
    p = charts_dir / "line_daily_sales.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning("グラフが見つかりません。run_pipeline.py を実行してください。")

with tab3:
    p = charts_dir / "bar_waste_loss.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
        st.caption(f"赤棒 = 廃棄ロス率 > {WASTE_ALERT_THRESHOLD*100:.0f}%（アラート閾値）")
    else:
        st.warning("グラフが見つかりません。run_pipeline.py を実行してください。")

st.divider()

# ── 廃棄ロス サマリーテーブル ───────────────────────────
st.subheader("店舗別 廃棄ロス集計")
if "waste_amount" in df.columns:
    waste_tbl = df.groupby("store_name").agg(
        売上合計=("sales_amount", "sum"),
        廃棄損失合計=("waste_amount", "sum"),
    ).copy()
    waste_tbl["廃棄ロス率(%)"] = (waste_tbl["廃棄損失合計"] / waste_tbl["売上合計"] * 100).round(2)
    waste_tbl["アラート"] = waste_tbl["廃棄ロス率(%)"].apply(
        lambda x: "⚠ アラート" if x > WASTE_ALERT_THRESHOLD * 100 else "✅ 正常"
    )
    waste_tbl["売上合計"] = waste_tbl["売上合計"].apply(lambda x: f"¥{x:,.0f}")
    waste_tbl["廃棄損失合計"] = waste_tbl["廃棄損失合計"].apply(lambda x: f"¥{x:,.0f}")
    waste_tbl = waste_tbl.sort_values("廃棄ロス率(%)", ascending=False)
    st.dataframe(waste_tbl, use_container_width=True)

st.divider()

# ── 分析レポート（展開表示） ─────────────────────────────
with st.expander("📋 分析レポートを見る", expanded=False):
    st.markdown(report_text)

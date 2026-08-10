"""小売 売上データ分析ダッシュボード — xlsx/csv 混在対応・列名マッピング版"""
import yaml
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

BASE = Path(__file__).parent
with open(BASE / "config.yml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

COL   = cfg.get("columns", {})
C_DATE  = COL.get("date",     "date")
C_STORE = COL.get("store",    "store")
C_SALES = COL.get("sales",    "sales")
C_COST  = COL.get("cost",     "cost")
C_CAT   = COL.get("category", "category")
ALERT_GM = cfg.get("alert_gross_margin_rate", 0.25)


@st.cache_data
def load_sample():
    return pd.read_csv(BASE / "sample_sales.csv", encoding="utf-8-sig")


def load_uploaded(file):
    name = file.name.lower()
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(file)
    return pd.read_csv(file, encoding="utf-8-sig")


def prep(df: pd.DataFrame) -> pd.DataFrame:
    df[C_DATE]  = pd.to_datetime(df[C_DATE], errors="coerce")
    for col in [C_SALES, C_COST]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["gross"]    = df[C_SALES] - df[C_COST]
    df["gm_rate"]  = (df["gross"] / df[C_SALES].replace(0, 1) * 100).round(1)
    return df.dropna(subset=[C_DATE])


# ── サイドバー ─────────────────────────────────────────────────
st.title("🛒 小売 売上データ分析ダッシュボード")
st.caption("2024年1月 | 3店舗 | サンプルデータ")

with st.sidebar:
    st.subheader("📂 データ入力")
    src = st.radio("データソース", ["サンプルデータを使用", "ファイルをアップロード"])

    if src == "ファイルをアップロード":
        uploaded = st.file_uploader("CSV または Excel (.xlsx)", type=["csv", "xlsx", "xls"])
        if uploaded:
            df_raw = load_uploaded(uploaded)
            st.success(f"✅ {uploaded.name} をロード ({len(df_raw)}行)")
        else:
            st.info("ファイルを選択してください")
            df_raw = load_sample()
    else:
        df_raw = load_sample()
        st.success(f"✅ サンプルデータをロード ({len(df_raw)}行)")

    st.divider()
    st.subheader("🔍 フィルター")
    df_all = prep(df_raw.copy())

    stores = sorted(df_all[C_STORE].dropna().unique()) if C_STORE in df_all.columns else []
    sel_stores = st.multiselect("店舗", stores, default=stores)

    categories = sorted(df_all[C_CAT].dropna().unique()) if C_CAT in df_all.columns else []
    sel_cats = st.multiselect("カテゴリ", categories, default=categories)

    date_min = df_all[C_DATE].min().date()
    date_max = df_all[C_DATE].max().date()
    date_range = st.date_input("集計期間", value=(date_min, date_max),
                               min_value=date_min, max_value=date_max)

# ── フィルタリング ──────────────────────────────────────────────
df = df_all.copy()
if sel_stores:
    df = df[df[C_STORE].isin(sel_stores)]
if sel_cats and C_CAT in df.columns:
    df = df[df[C_CAT].isin(sel_cats)]
if len(date_range) == 2:
    d0, d1 = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    df = df[(df[C_DATE] >= d0) & (df[C_DATE] <= d1)]

# ── KPI ────────────────────────────────────────────────────────
total_sales = df[C_SALES].sum()
total_cost  = df[C_COST].sum()
total_gross = df["gross"].sum()
gm_rate     = total_gross / total_sales * 100 if total_sales > 0 else 0
alert       = gm_rate < ALERT_GM * 100

c1, c2, c3, c4 = st.columns(4)
c1.metric("総売上",   f"¥{total_sales:,.0f}")
c2.metric("総原価",   f"¥{total_cost:,.0f}")
c3.metric("総粗利",   f"¥{total_gross:,.0f}")
c4.metric("粗利率",   f"{gm_rate:.1f}%",
          delta="⚠ アラート" if alert else "✅ 正常",
          delta_color="inverse" if alert else "normal")

if alert:
    st.warning(f"⚠ 粗利率 {gm_rate:.1f}% がアラートライン {ALERT_GM*100:.0f}% を下回っています")

st.divider()

# ── タブ ───────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📈 日次売上推移", "🏪 店舗別比較", "📋 データテーブル"])

with tab1:
    daily = df.groupby([C_DATE, C_STORE])[[C_SALES, "gross"]].sum().reset_index()
    fig = px.line(daily, x=C_DATE, y=C_SALES, color=C_STORE,
                  title="日次売上推移（店舗別）",
                  labels={C_DATE: "日付", C_SALES: "売上（円）", C_STORE: "店舗"})
    fig.update_traces(mode="lines+markers")
    st.plotly_chart(fig, use_container_width=True)

    fig2 = px.bar(daily, x=C_DATE, y="gross", color=C_STORE,
                  title="日次粗利推移（店舗別）",
                  labels={C_DATE: "日付", "gross": "粗利（円）", C_STORE: "店舗"},
                  barmode="group")
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    store_sum = df.groupby(C_STORE).agg(
        売上合計=(C_SALES, "sum"),
        粗利合計=("gross", "sum"),
        取引日数=(C_DATE, "nunique"),
    ).reset_index()
    store_sum["粗利率(%)"]  = (store_sum["粗利合計"] / store_sum["売上合計"] * 100).round(1)
    store_sum["1日平均売上"] = (store_sum["売上合計"] / store_sum["取引日数"]).round(0)
    store_sum["アラート"]   = store_sum["粗利率(%)"].apply(
        lambda x: "⚠ 要注意" if x < ALERT_GM * 100 else "✅ 正常"
    )

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(x=store_sum[C_STORE], y=store_sum["売上合計"],
                          name="売上合計", marker_color="#3b82f6"))
    fig3.add_trace(go.Bar(x=store_sum[C_STORE], y=store_sum["粗利合計"],
                          name="粗利合計", marker_color="#10b981"))
    fig3.update_layout(barmode="group", title="店舗別 売上・粗利合計",
                       xaxis_title="店舗", yaxis_title="金額（円）")
    st.plotly_chart(fig3, use_container_width=True)

    st.dataframe(store_sum[[C_STORE, "売上合計", "粗利合計", "粗利率(%)", "1日平均売上", "アラート"]],
                 use_container_width=True, hide_index=True)

with tab3:
    disp = df[[C_DATE, C_STORE, C_SALES, C_COST, "gross", "gm_rate"]].copy()
    disp.columns = ["日付", "店舗", "売上", "原価", "粗利", "粗利率(%)"]
    disp["日付"] = disp["日付"].dt.strftime("%Y-%m-%d")
    st.dataframe(disp.sort_values("日付", ascending=False),
                 use_container_width=True, hide_index=True)

st.divider()
st.caption(f"📐 アラートライン: 粗利率 {ALERT_GM*100:.0f}% ｜ config.yml で変更可能")

"""
C-21: サービス売上・原価分析ダッシュボード (Streamlit)
"""
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

st.set_page_config(
    page_title="サービス 売上・原価分析ダッシュボード",
    page_icon="💼",
    layout="wide",
)

BASE = Path(__file__).parent
CSV_PATH = BASE / "output" / "cleaned_revenue_cost_202401.csv"
REPORT_PATH = BASE / "output" / "analysis_report.md"
CHARTS_DIR = BASE / "output" / "charts"


@st.cache_data
def load_data():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["is_completed"] = df["is_completed"].astype(str).map(
        lambda x: True if x.lower() in ("true", "1") else False
    )
    for col in ["revenue", "direct_cost", "allocated_overhead", "total_cost",
                "gross_profit", "operating_profit", "gross_margin_ratio",
                "operating_margin_ratio", "revenue_per_hour", "hours_spent"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data
def load_report():
    if REPORT_PATH.exists():
        return REPORT_PATH.read_text(encoding="utf-8")
    return "レポートが見つかりません"


df_all = load_data()

st.title("💼 サービス 売上・原価分析ダッシュボード")
st.caption("2024年1〜3月 | ITサービス案件別売上・原価データ")

# サービス区分フィルター
service_types = sorted(df_all["service_type"].dropna().unique().tolist())
selected = st.multiselect("サービス区分フィルター", service_types, default=service_types)
df = df_all[df_all["service_type"].isin(selected)] if selected else df_all

# メトリクス
total_revenue = df["revenue"].sum()
avg_gm = (df["gross_profit"].sum() / total_revenue * 100) if total_revenue > 0 else 0
total_op = df["operating_profit"].sum()
red_count = (df["profit_flag"] == "赤字").sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("売上合計", f"¥{total_revenue:,.0f}")
c2.metric("平均粗利率", f"{avg_gm:.1f}%")
c3.metric("営業利益合計", f"¥{total_op:,.0f}",
          delta="注意" if total_op < 0 else None,
          delta_color="inverse" if total_op < 0 else "normal")
c4.metric("赤字案件数", f"{red_count}件",
          delta="要対応" if red_count > 0 else "問題なし",
          delta_color="inverse" if red_count > 0 else "normal")

st.divider()

tab1, tab2, tab3 = st.tabs(["サービス別利益率", "部門別売上", "売上構成比"])

with tab1:
    p = CHARTS_DIR / "bar_service_margin.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning("グラフなし。visualize.py を先に実行してください。")

with tab2:
    p = CHARTS_DIR / "bar_dept_revenue.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning("グラフなし")

with tab3:
    p = CHARTS_DIR / "pie_service_revenue_share.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning("グラフなし")

st.divider()

# サービス別集計テーブル
st.subheader("サービス別 収益サマリー")
svc_tbl = df.groupby("service_type").agg(
    案件数=("project_id", "count"),
    売上合計=("revenue", "sum"),
    粗利合計=("gross_profit", "sum"),
    営業利益合計=("operating_profit", "sum"),
    赤字件数=("profit_flag", lambda x: (x == "赤字").sum()),
).reset_index()
svc_tbl["粗利率(%)"] = (svc_tbl["粗利合計"] / svc_tbl["売上合計"].replace(0, np.nan) * 100).round(1)
svc_tbl["営業利益率(%)"] = (svc_tbl["営業利益合計"] / svc_tbl["売上合計"].replace(0, np.nan) * 100).round(1)
svc_tbl = svc_tbl.sort_values("粗利率(%)", ascending=False)
for col in ["売上合計", "粗利合計", "営業利益合計"]:
    svc_tbl[col] = svc_tbl[col].apply(lambda x: f"¥{x:,.0f}")
st.dataframe(svc_tbl, use_container_width=True)

st.divider()

# 赤字・低収益案件アラート
alert_df = df[df["profit_flag"].isin(["赤字", "低収益"])][
    ["project_id", "client_name", "service_type", "department",
     "contract_month", "revenue", "operating_margin_ratio", "profit_flag"]
].copy()
if len(alert_df) > 0:
    st.subheader(f"要注意案件 ({len(alert_df)}件)")
    alert_df["revenue"] = alert_df["revenue"].apply(lambda x: f"¥{x:,.0f}")
    alert_df["operating_margin_ratio"] = alert_df["operating_margin_ratio"].apply(
        lambda x: f"{x*100:.1f}%" if pd.notna(x) else "N/A"
    )
    st.dataframe(alert_df, use_container_width=True)

st.divider()

with st.expander("分析レポートを見る", expanded=False):
    st.markdown(load_report())

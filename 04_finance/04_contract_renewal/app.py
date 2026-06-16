"""
C-31: 契約更新アラート・期限管理パイプライン Streamlit ダッシュボード
"""
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="契約更新アラートダッシュボード",
    page_icon="📋",
    layout="wide",
)

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"

STATUS_ORDER = ["期限切れ", "緊急", "警告", "正常"]
STATUS_COLORS = {
    "期限切れ": "red",
    "緊急":     "orange",
    "警告":     "yellow",
    "正常":     "green",
}


@st.cache_data
def load_data() -> pd.DataFrame:
    path = OUTPUT_DIR / "cleaned_contracts_202401.csv"
    df = pd.read_csv(path, encoding="utf-8-sig")
    for col in ["annual_premium", "days_to_expiry", "contract_years"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "end_date" in df.columns:
        df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
    if "start_date" in df.columns:
        df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    return df


@st.cache_data
def load_report() -> str:
    p = OUTPUT_DIR / "analysis_report.md"
    return p.read_text(encoding="utf-8") if p.exists() else "レポートが見つかりません。"


def fmt_yen(val: float) -> str:
    """金額を日本円形式で表示（バックスラッシュY記号なし）"""
    return f"{val:,.0f} 円"


# --- データ読み込み ---
try:
    df_all = load_data()
except FileNotFoundError:
    st.error("cleaned_contracts_202401.csv が見つかりません。cleanse.py を先に実行してください。")
    st.stop()

report_text = load_report()

# --- タイトル ---
st.title("📋 金融・保険 契約更新アラートダッシュボード")
st.caption("基準日: 2024年2月1日 | C-31 契約更新アラート・期限管理パイプライン")

# --- 担当者フィルター ---
all_agents = sorted(df_all["agent_name"].dropna().unique().tolist()) if "agent_name" in df_all.columns else []
selected_agents = st.multiselect(
    "担当者フィルター",
    options=all_agents,
    default=all_agents,
)
df = df_all[df_all["agent_name"].isin(selected_agents)] if selected_agents else df_all

# --- KPI 4つ ---
total_contracts = len(df)
expired_count = (df["renewal_status"] == "期限切れ").sum() if "renewal_status" in df.columns else 0
urgent_count = (df["renewal_status"] == "緊急").sum() if "renewal_status" in df.columns else 0
total_premium = df["annual_premium"].sum() if "annual_premium" in df.columns else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("総契約数", f"{total_contracts:,} 件")
c2.metric(
    "期限切れ件数",
    f"{expired_count:,} 件",
    delta="要対応" if expired_count > 0 else "なし",
    delta_color="inverse" if expired_count > 0 else "off",
)
c3.metric(
    "緊急件数（30日以内）",
    f"{urgent_count:,} 件",
    delta="要対応" if urgent_count > 0 else "なし",
    delta_color="inverse" if urgent_count > 0 else "off",
)
c4.metric("年間保険料合計", fmt_yen(total_premium))

st.divider()

# --- 3タブ ---
tab1, tab2, tab3 = st.tabs(["更新ステータス", "担当者別アラート", "保険種別構成"])

charts_dir = OUTPUT_DIR / "charts"

with tab1:
    st.subheader("更新ステータス別件数")
    p = charts_dir / "bar_renewal_status.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning("グラフなし。visualize.py を実行してください。")

    st.subheader("更新ステータス別サマリー")
    if "renewal_status" in df.columns:
        summary = df.groupby("renewal_status").agg(
            件数=("contract_no", "count"),
            年間保険料合計=("annual_premium", "sum"),
            年間保険料平均=("annual_premium", "mean"),
        ).reindex(STATUS_ORDER).fillna(0)
        summary["構成比(%)"] = (summary["件数"] / summary["件数"].sum() * 100).round(1)
        summary["年間保険料合計"] = summary["年間保険料合計"].map("{:,.0f}".format)
        summary["年間保険料平均"] = summary["年間保険料平均"].map("{:,.0f}".format)
        st.dataframe(summary, use_container_width=True)

with tab2:
    st.subheader("担当者別 アラート件数（期限切れ+緊急）")
    p = charts_dir / "bar_agent_alert.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning("グラフなし。visualize.py を実行してください。")

    if "agent_name" in df.columns and "renewal_status" in df.columns:
        agent_tbl = df.groupby("agent_name").agg(
            担当契約数=("contract_no", "count"),
            期限切れ=("renewal_status", lambda x: (x == "期限切れ").sum()),
            緊急=("renewal_status", lambda x: (x == "緊急").sum()),
            警告=("renewal_status", lambda x: (x == "警告").sum()),
            正常=("renewal_status", lambda x: (x == "正常").sum()),
        )
        agent_tbl["アラート計"] = agent_tbl["期限切れ"] + agent_tbl["緊急"]
        agent_tbl = agent_tbl.sort_values("アラート計", ascending=False)
        st.dataframe(agent_tbl, use_container_width=True)

with tab3:
    st.subheader("保険種別 件数構成")
    p = charts_dir / "pie_insurance_type.png"
    if p.exists():
        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.image(str(p), use_container_width=True)
        with col_right:
            if "insurance_type" in df.columns:
                ins_tbl = df.groupby("insurance_type").agg(
                    件数=("contract_no", "count"),
                    期限切れ=("renewal_status", lambda x: (x == "期限切れ").sum()),
                    緊急=("renewal_status", lambda x: (x == "緊急").sum()),
                    年間保険料合計=("annual_premium", "sum"),
                )
                ins_tbl["アラート率(%)"] = (
                    (ins_tbl["期限切れ"] + ins_tbl["緊急"]) / ins_tbl["件数"] * 100
                ).round(1)
                ins_tbl["年間保険料合計"] = ins_tbl["年間保険料合計"].map("{:,.0f}".format)
                st.dataframe(ins_tbl, use_container_width=True)
    else:
        st.warning("グラフなし。visualize.py を実行してください。")

st.divider()

# --- 期限切れ・緊急の契約明細テーブル ---
st.subheader("期限切れ・緊急 契約明細")
if "renewal_status" in df.columns:
    alert_df = df[df["renewal_status"].isin(["期限切れ", "緊急"])].copy()
    if len(alert_df) > 0:
        alert_df_sorted = alert_df.sort_values("days_to_expiry")
        disp_cols = [c for c in [
            "contract_no", "customer_code", "insurance_type",
            "end_date", "days_to_expiry", "annual_premium",
            "agent_name", "renewal_status"
        ] if c in alert_df_sorted.columns]
        st.dataframe(alert_df_sorted[disp_cols].head(200), use_container_width=True)
    else:
        st.info("アラート対象の契約はありません。")

st.divider()

# --- 分析レポート expander ---
with st.expander("分析レポートを見る", expanded=False):
    st.markdown(report_text)

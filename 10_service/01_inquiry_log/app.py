"""
B-40 サービス 問い合わせログ分析ダッシュボード（Streamlit）
"""
import streamlit as st
import pandas as pd
import yaml
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT  = BASE / "output"
CSV_PATH = OUT / "cleaned_inquiry_202401.csv"
CFG_PATH = BASE / "config.yml"
RPT_PATH = OUT / "analysis_report.md"

st.title("📞 B-40 サービス 問い合わせログ分析ダッシュボード")
st.caption("B-40 | 2024年1月 | 問い合わせログ | カテゴリ別・担当者別・時間帯別分析")


@st.cache_data
def load_inquiry_log_data() -> pd.DataFrame:
    """B-40専用ローダー（キャッシュキー衝突防止）"""
    if not CSV_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["received_at"] = pd.to_datetime(df["received_at"], format="%Y-%m-%d %H:%M", errors="coerce")
    df["response_minutes"] = pd.to_numeric(df["response_minutes"], errors="coerce")
    return df


@st.cache_data
def load_inquiry_log_config() -> dict:
    """B-40 設定ローダー"""
    if not CFG_PATH.exists():
        return {"response_time_alert_minutes": 60, "resolution_rate_alert": 0.8}
    with open(CFG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


df_all = load_inquiry_log_data()
cfg = load_inquiry_log_config()

if df_all.empty:
    st.error("クレンジング済みデータが見つかりません。cleanse.py を先に実行してください。")
    st.stop()

# サイドバーフィルター
with st.sidebar:
    st.header("🔍 フィルター")
    categories = sorted(df_all["category"].unique().tolist())
    sel_cats = st.multiselect("カテゴリ", categories, default=categories)
    channels = sorted(df_all["channel"].unique().tolist())
    sel_ch = st.multiselect("チャネル", channels, default=channels)

df = df_all[df_all["category"].isin(sel_cats) & df_all["channel"].isin(sel_ch)]

# メトリクス
total = len(df)
resolution_rate = df["is_resolved"].mean() * 100 if total > 0 else 0
escalation_rate = df["is_escalated"].mean() * 100 if total > 0 else 0
avg_resp = df["response_minutes"].mean() if total > 0 else 0
alert_thresh = cfg.get("response_time_alert_minutes", 60)
alert_count = int((df["response_minutes"] > alert_thresh).sum()) if total > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("総問い合わせ数", f"{total:,}件")
col2.metric("解決率", f"{resolution_rate:.1f}%")
col3.metric("エスカレ率", f"{escalation_rate:.1f}%")
col4.metric("平均対応時間", f"{avg_resp:.1f}分")
col5.metric("⚠長時間対応件数", f"{alert_count}件")

st.divider()

# タブ
tab1, tab2, tab3 = st.tabs(["📊 カテゴリ別", "👤 担当者別", "🕐 時間帯別"])

with tab1:
    st.subheader("カテゴリ別問い合わせ分析")
    if total > 0:
        cat_grp = df.groupby("category").agg(
            件数=("inquiry_id", "count"),
            平均対応時間=("response_minutes", "mean"),
            解決率=("is_resolved", "mean"),
            エスカレ率=("is_escalated", "mean"),
        ).reset_index().sort_values("件数", ascending=False)
        cat_grp["割合(%)"] = (cat_grp["件数"] / total * 100).round(1)
        cat_grp["平均対応時間(分)"] = cat_grp["平均対応時間"].round(1)
        cat_grp["解決率(%)"] = (cat_grp["解決率"] * 100).round(1)
        cat_grp["エスカレ率(%)"] = (cat_grp["エスカレ率"] * 100).round(1)

        # Plotly不使用・Streamlit純正チャート
        st.bar_chart(cat_grp.set_index("category")["件数"])

        display_cols = ["category", "件数", "割合(%)", "平均対応時間(分)", "解決率(%)", "エスカレ率(%)"]
        st.dataframe(cat_grp[display_cols].reset_index(drop=True), use_container_width=True)

with tab2:
    st.subheader("担当者別パフォーマンス")
    if total > 0:
        op_grp = df.groupby(["operator_id", "operator_name"]).agg(
            担当件数=("inquiry_id", "count"),
            平均対応時間=("response_minutes", "mean"),
            解決率=("is_resolved", "mean"),
            エスカレ率=("is_escalated", "mean"),
        ).reset_index()
        op_grp["平均対応時間(分)"] = op_grp["平均対応時間"].round(1)
        op_grp["解決率(%)"] = (op_grp["解決率"] * 100).round(1)
        op_grp["エスカレ率(%)"] = (op_grp["エスカレ率"] * 100).round(1)
        op_grp = op_grp.sort_values("解決率(%)")

        st.bar_chart(op_grp.set_index("operator_name")["解決率(%)"])

        display_cols = ["operator_id", "operator_name", "担当件数", "平均対応時間(分)", "解決率(%)", "エスカレ率(%)"]
        st.dataframe(op_grp[display_cols].reset_index(drop=True), use_container_width=True)

with tab3:
    st.subheader("時間帯別受付傾向")
    if total > 0:
        df_copy = df.copy()
        df_copy["hour"] = df_copy["received_at"].dt.hour
        hour_grp = df_copy.groupby("hour")["inquiry_id"].count().reindex(range(9, 18), fill_value=0)
        peak_hour = int(hour_grp.idxmax())

        hour_df = hour_grp.rename_axis("時間帯").reset_index(name="件数")
        hour_df["時間帯"] = hour_df["時間帯"].astype(str) + "時"
        st.bar_chart(hour_df.set_index("時間帯")["件数"])

        st.info(f"ピーク時間帯: **{peak_hour}時** ({hour_grp[peak_hour]}件)")

# 分析レポート
with st.expander("📄 詳細分析レポート", expanded=False):
    if RPT_PATH.exists():
        st.markdown(RPT_PATH.read_text(encoding="utf-8"))
    else:
        st.info("レポートが見つかりません。analyze.py を実行してください。")

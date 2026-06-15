"""
B-15 Streamlit Dashboard — 問い合わせログ分析
"""
import streamlit as st
import pandas as pd
import yaml
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm

# 日本語フォント設定
jp_fonts = ["MS Gothic", "Meiryo", "IPAexGothic", "Noto Sans CJK JP", "DejaVu Sans"]
available = {f.name for f in fm.fontManager.ttflist}
for font in jp_fonts:
    if font in available:
        plt.rcParams["font.family"] = font
        break

BASE = Path(__file__).resolve().parent
OUT  = BASE / "output"
CSV_PATH = OUT / "cleaned_inquiry_202401.csv"
CFG_PATH = BASE / "config.yml"
RPT_PATH = OUT / "analysis_report.md"

st.set_page_config(page_title="B-15 問い合わせログ分析", layout="wide", page_icon="📞")

@st.cache_data
def load_data():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["received_at"] = pd.to_datetime(df["received_at"], format="%Y-%m-%d %H:%M", errors="coerce")
    df["response_minutes"] = pd.to_numeric(df["response_minutes"], errors="coerce")
    return df

@st.cache_data
def load_config():
    with open(CFG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)

if not CSV_PATH.exists():
    st.error("クレンジング済みデータが見つかりません。output/cleanse.py を先に実行してください。")
    st.stop()

df_all = load_data()
cfg = load_config()

st.title("📞 B-15 問い合わせログ分析ダッシュボード")
st.caption("2024年1月 — 500件問い合わせログ | キーワードベース自動分類")

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
alert_count = (df["response_minutes"] > cfg["response_time_alert_minutes"]).sum() if total > 0 else 0

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

        # チャート
        fig, ax1 = plt.subplots(figsize=(10, 5))
        bars = ax1.bar(cat_grp["category"], cat_grp["件数"], color="#4C72B0", alpha=0.8)
        ax1.set_ylabel("件数", color="#4C72B0")
        ax1.tick_params(axis="x", rotation=20)
        ax2 = ax1.twinx()
        line = ax2.plot(cat_grp["category"], cat_grp["平均対応時間(分)"], color="#DD8452", marker="o", linewidth=2)
        ax2.set_ylabel("平均対応時間(分)", color="#DD8452")
        h1 = mpatches.Patch(color="#4C72B0", alpha=0.8, label="件数")
        ax1.legend(handles=[h1] + line, loc="upper right")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

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
        op_grp = op_grp.sort_values("解決率(%)")  # 解決率低い順

        # チャート
        labels = [f"{r['operator_id']}\n{r['operator_name']}" for _, r in op_grp.iterrows()]
        colors = ["#DD4444" if r["解決率(%)"] < cfg["resolution_rate_alert"] * 100 else "#4C72B0" for _, r in op_grp.iterrows()]
        fig, ax1 = plt.subplots(figsize=(12, 5))
        ax1.bar(labels, op_grp["解決率(%)"], color=colors, alpha=0.8)
        ax1.axhline(y=cfg["resolution_rate_alert"] * 100, color="red", linestyle="--", linewidth=1.5)
        ax1.set_ylabel("解決率(%)")
        ax1.set_ylim(0, 105)
        ax2 = ax1.twinx()
        line = ax2.plot(labels, op_grp["平均対応時間(分)"], color="#DD8452", marker="o", linewidth=2)
        ax2.set_ylabel("平均対応時間(分)", color="#DD8452")
        h1 = mpatches.Patch(color="#4C72B0", alpha=0.8, label="解決率(%)")
        h2 = mpatches.Patch(color="#DD4444", alpha=0.8, label="要改善")
        ax1.legend(handles=[h1, h2] + line, loc="lower right")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        display_cols = ["operator_id", "operator_name", "担当件数", "平均対応時間(分)", "解決率(%)", "エスカレ率(%)"]
        st.dataframe(op_grp[display_cols].reset_index(drop=True), use_container_width=True)

with tab3:
    st.subheader("時間帯別受付傾向")
    if total > 0:
        df_copy = df.copy()
        df_copy["hour"] = df_copy["received_at"].dt.hour
        hour_grp = df_copy.groupby("hour")["inquiry_id"].count().reindex(range(9, 18), fill_value=0)
        peak_hour = int(hour_grp.idxmax())

        colors3 = ["#DD4444" if h == peak_hour else "#4C72B0" for h in hour_grp.index]
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar([f"{h}時" for h in hour_grp.index], hour_grp.values, color=colors3, alpha=0.85)
        ax.set_ylabel("問い合わせ件数")
        ax.set_title(f"ピーク時間帯: {peak_hour}時 ({hour_grp[peak_hour]}件)")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        st.info(f"ピーク時間帯: **{peak_hour}時** ({hour_grp[peak_hour]}件)")

# 分析レポートエキスパンダー
if RPT_PATH.exists():
    with st.expander("📄 詳細分析レポート"):
        with open(RPT_PATH, encoding="utf-8") as f:
            st.markdown(f.read())

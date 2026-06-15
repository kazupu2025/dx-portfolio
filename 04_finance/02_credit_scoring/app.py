"""
B-11: 与信スコアリング Streamlit ダッシュボード
"""
from pathlib import Path
import pandas as pd
import streamlit as st
import yaml

BASE = Path(__file__).parent
OUT = BASE / "output"
CHARTS = OUT / "charts"

with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

st.set_page_config(
    page_title="B-11 与信スコアリング ダッシュボード",
    page_icon="💳",
    layout="wide",
)

st.title("💳 B-11 与信スコアリング データ整備ダッシュボード")
st.caption("スコアカード方式による申込者リスク分類・職業別分析 | 2024年1月")

# --- データ読み込み ---
csv_path = OUT / "cleaned_credit_202401.csv"
if not csv_path.exists():
    st.error(f"クレンジング済みCSVが見つかりません: {csv_path}\n`output/cleanse.py` を先に実行してください。")
    st.stop()

df = pd.read_csv(csv_path, encoding="utf-8-sig")

# --- サイドバー: リスク分類フィルター ---
st.sidebar.header("フィルター")
risk_options = ["高リスク", "中リスク", "低リスク"]
selected_risks = st.sidebar.multiselect(
    "リスク分類",
    options=risk_options,
    default=risk_options,
)
if selected_risks:
    filtered = df[df["risk_category"].isin(selected_risks)]
else:
    filtered = df.copy()

# --- メトリクス ---
total = len(filtered)
avg_score = filtered["credit_score"].mean() if total > 0 else 0
high_risk_rate = (filtered["risk_category"] == "高リスク").mean() * 100 if total > 0 else 0
alert_count = (filtered["debt_income_ratio"] > config["debt_income_alert_ratio"]).sum()
approved_count = (filtered["risk_category"] == "低リスク").sum()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("総申込数", f"{total:,} 件")
col2.metric("平均スコア", f"{avg_score:.1f} 点")
col3.metric("高リスク率", f"{high_risk_rate:.1f} %")
col4.metric("⚠ 高負債比率件数", f"{alert_count} 件")
col5.metric("承認推奨件数（低リスク）", f"{approved_count} 件")

st.divider()

# --- タブ ---
tab1, tab2, tab3 = st.tabs(["📊 リスク分布", "👔 職業別スコア", "📈 スコアヒストグラム"])

chart1 = CHARTS / "bar_risk_distribution.png"
chart2 = CHARTS / "bar_occupation_score.png"
chart3 = CHARTS / "hist_credit_score.png"

with tab1:
    st.subheader("リスク分類別 申込者数")
    if chart1.exists():
        st.image(str(chart1))
    else:
        st.warning("チャートが存在しません。`output/visualize.py` を実行してください。")

with tab2:
    st.subheader("職業別 平均与信スコア（高リスク/中リスク閾値ライン付き）")
    if chart2.exists():
        st.image(str(chart2))
    else:
        st.warning("チャートが存在しません。")

with tab3:
    st.subheader("与信スコア ヒストグラム（10点刻み）")
    if chart3.exists():
        st.image(str(chart3))
    else:
        st.warning("チャートが存在しません。")

st.divider()

# --- リスク分類別サマリーテーブル ---
st.subheader("リスク分類別サマリー")
risk_order = ["高リスク", "中リスク", "低リスク"]
summary = (
    filtered.groupby("risk_category")
    .agg(
        件数=("application_id", "count"),
        平均スコア=("credit_score", "mean"),
        平均年収_万円=("annual_income", "mean"),
        高負債比率件数=("debt_income_ratio", lambda x: (x > config["debt_income_alert_ratio"]).sum()),
    )
    .reindex([r for r in risk_order if r in filtered["risk_category"].unique()])
    .reset_index()
)
summary["割合(%)"] = (summary["件数"] / total * 100).round(1)
summary["平均スコア"] = summary["平均スコア"].round(1)
summary["平均年収_万円"] = summary["平均年収_万円"].round(0).astype(int)
st.dataframe(summary, use_container_width=True, hide_index=True)

# --- 分析レポートエキスパンダー ---
report_path = OUT / "credit_report_202401.txt"
with st.expander("📄 分析レポート（テキスト全文）"):
    if report_path.exists():
        st.text(report_path.read_text(encoding="utf-8"))
    else:
        st.warning("レポートが存在しません。`output/analyze.py` を実行してください。")

st.caption("B-11 与信スコアリング | Pipeline Pattern | 架空データによるデモシステム")

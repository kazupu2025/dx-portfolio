# -*- coding: utf-8 -*-
"""
C-25: 生産計画 vs 実績 差異分析パイプライン
Streamlit ダッシュボード
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import streamlit as st
from pathlib import Path

matplotlib.rcParams["font.family"] = "MS Gothic"

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CLEANED_CSV = OUTPUT_DIR / "cleaned_production_202401.csv"
LINE_SUMMARY_CSV = OUTPUT_DIR / "line_summary_202401.csv"
REPORT_MD = OUTPUT_DIR / "analysis_report.md"
CHARTS_DIR = OUTPUT_DIR / "charts"

st.set_page_config(
    page_title="製造 生産計画差異ダッシュボード",
    page_icon="🏭",
    layout="wide",
)

st.title("🏭 製造 生産計画差異ダッシュボード")
st.caption("C-25: 生産計画 vs 実績 差異分析パイプライン | 2024年1月")


@st.cache_data
def load_data() -> pd.DataFrame:
    if not CLEANED_CSV.exists():
        st.error(f"クレンジング済みCSVが見つかりません: {CLEANED_CSV}\ncleanse.py を先に実行してください。")
        st.stop()
    return pd.read_csv(CLEANED_CSV, encoding="utf-8-sig", parse_dates=["date"])


@st.cache_data
def load_line_summary() -> pd.DataFrame | None:
    if LINE_SUMMARY_CSV.exists():
        return pd.read_csv(LINE_SUMMARY_CSV, encoding="utf-8-sig")
    return None


df_all = load_data()

# ---- ラインフィルター ----
all_lines = sorted(df_all["line_name"].unique())
selected_lines = st.multiselect(
    "製造ラインを選択（複数選択可）",
    options=all_lines,
    default=all_lines,
)

if not selected_lines:
    st.warning("少なくとも1つのラインを選択してください。")
    st.stop()

df = df_all[df_all["line_name"].isin(selected_lines)]

# ---- KPI ----
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("総計画数量", f"{int(df['planned_qty'].sum()):,}")
with col2:
    st.metric("総実績数量", f"{int(df['actual_qty'].sum()):,}")
with col3:
    avg_ach = df["achievement_rate"].mean()
    st.metric("平均達成率", f"{avg_ach*100:.1f}%")
with col4:
    avg_def = df["defect_rate"].mean()
    st.metric("平均不良率", f"{avg_def*100:.2f}%")

st.divider()

# ---- 3タブ ----
tab1, tab2, tab3 = st.tabs(["達成率分析", "不良率分析", "計画vs実績散布図"])

with tab1:
    st.subheader("ライン別 平均達成率")
    grp_ach = df.groupby("line_name")["achievement_rate"].mean().reset_index()
    grp_ach = grp_ach.sort_values("line_name")

    fig1, ax1 = plt.subplots(figsize=(7, 4))
    bars1 = ax1.bar(grp_ach["line_name"], grp_ach["achievement_rate"] * 100,
                    color="#4C72B0", edgecolor="white", alpha=0.85)
    ax1.axhline(y=100, color="red", linestyle="--", linewidth=1.5, label="計画達成ライン (100%)")
    ax1.set_xlabel("製造ライン")
    ax1.set_ylabel("平均達成率 (%)")
    ax1.set_title("ライン別 平均達成率")
    ax1.legend()
    ax1.bar_label(bars1, fmt="%.1f%%", padding=3, fontsize=9)
    fig1.tight_layout()
    st.pyplot(fig1)
    plt.close(fig1)

    st.subheader("達成率分布（ライン別）")
    st.dataframe(
        grp_ach.rename(columns={"line_name": "ライン名", "achievement_rate": "平均達成率"}).assign(
            平均達成率=lambda x: (x["平均達成率"] * 100).round(1).astype(str) + "%"
        ),
        use_container_width=True,
    )

with tab2:
    st.subheader("カテゴリ別 平均不良率")
    grp_def = df.groupby("category")["defect_rate"].mean().reset_index()
    grp_def = grp_def.sort_values("defect_rate", ascending=False)

    fig2, ax2 = plt.subplots(figsize=(7, 4))
    bars2 = ax2.bar(grp_def["category"], grp_def["defect_rate"] * 100,
                    color="#DD8452", edgecolor="white", alpha=0.85)
    ax2.set_xlabel("製品カテゴリ")
    ax2.set_ylabel("平均不良率 (%)")
    ax2.set_title("カテゴリ別 平均不良率")
    ax2.bar_label(bars2, fmt="%.2f%%", padding=3, fontsize=9)
    fig2.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

    st.subheader("不良率詳細（カテゴリ別）")
    st.dataframe(
        grp_def.rename(columns={"category": "カテゴリ", "defect_rate": "平均不良率"}).assign(
            平均不良率=lambda x: (x["平均不良率"] * 100).round(3).astype(str) + "%"
        ),
        use_container_width=True,
    )

with tab3:
    st.subheader("計画数量 vs 実績数量 散布図")
    lines_list = sorted(df["line_name"].unique())
    colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B2"]

    fig3, ax3 = plt.subplots(figsize=(6, 5))
    for i, line in enumerate(lines_list):
        sub = df[df["line_name"] == line]
        ax3.scatter(sub["planned_qty"], sub["actual_qty"],
                    alpha=0.5, s=20, color=colors[i % len(colors)], label=line)
    max_val = max(df["planned_qty"].max(), df["actual_qty"].max()) * 1.05
    ax3.plot([0, max_val], [0, max_val], "k--", linewidth=1, label="計画=実績ライン")
    ax3.set_xlabel("計画数量")
    ax3.set_ylabel("実績数量")
    ax3.set_title("計画数量 vs 実績数量")
    ax3.legend(loc="upper left", fontsize=8)
    ax3.set_xlim(0, max_val)
    ax3.set_ylim(0, max_val)
    fig3.tight_layout()
    st.pyplot(fig3)
    plt.close(fig3)

st.divider()

# ---- サマリーテーブル（ライン別）----
st.subheader("ライン別サマリーテーブル")
line_summary = load_line_summary()
if line_summary is not None:
    filtered_summary = line_summary[line_summary["line_name"].isin(selected_lines)] if "line_name" in line_summary.columns else line_summary
    st.dataframe(filtered_summary, use_container_width=True)
else:
    # analyze.py未実行の場合はインラインで集計
    grp_table = df.groupby("line_name").agg(
        計画数量合計=("planned_qty", "sum"),
        実績数量合計=("actual_qty", "sum"),
        差異数量=("variance_qty", "sum"),
        平均達成率=("achievement_rate", "mean"),
        平均不良率=("defect_rate", "mean"),
    ).reset_index().rename(columns={"line_name": "ライン名"})
    grp_table["平均達成率"] = (grp_table["平均達成率"] * 100).round(1).astype(str) + "%"
    grp_table["平均不良率"] = (grp_table["平均不良率"] * 100).round(2).astype(str) + "%"
    st.dataframe(grp_table, use_container_width=True)

# ---- 分析レポートexpander ----
st.divider()
with st.expander("分析レポートを表示"):
    if REPORT_MD.exists():
        st.markdown(REPORT_MD.read_text(encoding="utf-8"))
    else:
        st.info("analyze.py を実行するとレポートが表示されます。")

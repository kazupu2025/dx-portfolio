import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="教育・研修 講師稼働ダッシュボード",
    page_icon="📚",
    layout="wide",
)

BASE = Path(__file__).parent


@st.cache_data
def load_data():
    p = BASE / "output" / "cleaned_instructor_202401.csv"
    df = pd.read_csv(p, encoding="utf-8-sig")
    for col in ["lesson_count", "lesson_hours", "lesson_cost", "attendee_count",
                "hourly_rate", "cost_per_attendee"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if "session_date" in df.columns:
        df["session_date"] = pd.to_datetime(df["session_date"], errors="coerce")
    return df


@st.cache_data
def load_report():
    p = BASE / "output" / "analysis_report.md"
    return p.read_text(encoding="utf-8") if p.exists() else "レポートが見つかりません"


df_all = load_data()
report_text = load_report()

st.title("📚 教育・研修 講師稼働ダッシュボード")
st.caption("2024年1月 | 講師稼働・コマ数管理パイプライン")

# --- 専門分野フィルター ---
specialties = sorted(df_all["specialty"].dropna().unique().tolist()) if "specialty" in df_all.columns else []
selected_specialties = st.multiselect("専門分野フィルター", specialties, default=specialties)
df = df_all[df_all["specialty"].isin(selected_specialties)] if selected_specialties else df_all

# --- KPIメトリクス ---
total_lessons = int(df["lesson_count"].sum()) if "lesson_count" in df.columns else 0
total_attendees = int(df["attendee_count"].sum()) if "attendee_count" in df.columns else 0
total_cost = float(df["lesson_cost"].sum()) if "lesson_cost" in df.columns else 0.0
avg_cost_per_attendee = (
    total_cost / total_attendees if total_attendees > 0 else 0.0
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("総コマ数", f"{total_lessons:,} コマ")
c2.metric("総受講者数", f"{total_attendees:,} 名")
c3.metric("総講師コスト", f"{total_cost:,.0f} 円")
c4.metric("平均受講者1名あたりコスト", f"{avg_cost_per_attendee:,.0f} 円")

st.divider()

# --- グラフタブ ---
tab1, tab2, tab3 = st.tabs(["コマ数上位講師", "専門分野別コスト", "雇用区分別コスト比率"])
charts_dir = BASE / "output" / "charts"

with tab1:
    p = charts_dir / "bar_instructor_lessons_top10.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning("グラフが見つかりません。visualize.py を実行してください。")

with tab2:
    p = charts_dir / "bar_specialty_cost.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning("グラフが見つかりません。visualize.py を実行してください。")

with tab3:
    p = charts_dir / "pie_employment_cost_share.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning("グラフが見つかりません。visualize.py を実行してください。")

st.divider()

# --- 専門分野別サマリーテーブル ---
st.subheader("専門分野別 コスト・受講者サマリー")
if "specialty" in df.columns and "lesson_cost" in df.columns:
    sp_tbl = df.groupby("specialty").agg(
        総コマ数=("lesson_count", "sum"),
        総受講者数=("attendee_count", "sum"),
        総コスト=("lesson_cost", "sum"),
    ).copy()
    sp_tbl["受講者1人あたりコスト(円)"] = (
        sp_tbl["総コスト"] / sp_tbl["総受講者数"].replace(0, 1)
    ).round(0)
    sp_tbl = sp_tbl.sort_values("総コスト", ascending=False)
    sp_tbl["総コスト"] = sp_tbl["総コスト"].apply(lambda x: f"{x:,.0f}")
    sp_tbl["受講者1人あたりコスト(円)"] = sp_tbl["受講者1人あたりコスト(円)"].apply(lambda x: f"{x:,.0f}")
    st.dataframe(sp_tbl, use_container_width=True)

st.divider()

# --- 分析レポート ---
with st.expander("分析レポートを見る", expanded=False):
    st.markdown(report_text)

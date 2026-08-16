"""
B-23 物流 ドライバー勤怠・拘束時間管理ダッシュボード（Streamlit）
起動: cd 05_logistics/03_driver_attendance && streamlit run app.py
"""
import streamlit as st
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CSV_PATH = OUTPUT_DIR / "cleaned_driver_202401.csv"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"


@st.cache_data
def load_data():
    if not CSV_PATH.exists():
        return None
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["confinement_over_flag"] = df["confinement_over_flag"].astype(bool)
    df["work_over_flag"] = df["work_over_flag"].astype(bool)
    return df


st.title("🚛 B-23 物流 ドライバー勤怠・拘束時間管理ダッシュボード")
st.caption("B-23 | 2024年1月 | 乗務件数・違反率・拘束時間・営業所別KPI")

df = load_data()

if df is None:
    st.error("データが見つかりません。パイプラインを実行してください。")
    st.stop()

# --- サイドバー: フィルター ---
with st.sidebar:
    st.header("🔍 フィルター")
    all_offices = sorted(df["office"].dropna().unique().tolist())
    selected_offices = st.multiselect("営業所選択", options=all_offices, default=all_offices)
    all_ops = sorted(df["operation_type"].dropna().unique().tolist())
    selected_ops = st.multiselect("運行区分選択", options=all_ops, default=all_ops)

# フィルタリング
if selected_offices and selected_ops:
    filtered = df[df["office"].isin(selected_offices) & df["operation_type"].isin(selected_ops)]
else:
    filtered = df.copy()

# --- KPI メトリクス ---
total_rides = len(filtered)
violation_count = (filtered["violation_flag"] == "違反").sum()
violation_rate = violation_count / total_rides if total_rides > 0 else 0
avg_confinement = filtered["confinement_hours"].mean() if "confinement_hours" in filtered.columns else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("総乗務件数", f"{total_rides:,} 件")
col2.metric("違反件数", f"{violation_count:,} 件")
col3.metric("違反率", f"{violation_rate:.1%}")
col4.metric("平均拘束時間", f"{avg_confinement:.2f} h")

st.divider()

# --- グラフ ---
tab1, tab2, tab3 = st.tabs(["🏢 営業所別違反率", "🚗 運行区分別距離", "👤 違反上位ドライバー"])

with tab1:
    chart_office = CHARTS_DIR / "bar_office_violation_rate.png"
    if chart_office.exists():
        st.image(str(chart_office), use_container_width=True)
    else:
        grp = filtered.groupby("office")["violation_flag"].apply(
            lambda x: (x == "違反").mean() * 100
        )
        st.bar_chart(grp)

with tab2:
    chart_pie = CHARTS_DIR / "pie_operation_distance.png"
    if chart_pie.exists():
        st.image(str(chart_pie), use_container_width=True)
    else:
        grp = filtered.groupby("operation_type")["distance_km"].sum()
        st.bar_chart(grp)

with tab3:
    chart_driver = CHARTS_DIR / "bar_driver_violation_top10.png"
    if chart_driver.exists():
        st.image(str(chart_driver), use_container_width=True)
    else:
        grp = (
            filtered[filtered["violation_flag"] == "違反"]
            .groupby(["driver_id", "name"])
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
            .head(10)
            .set_index("name")["count"]
        )
        st.bar_chart(grp)

st.divider()

# --- 詳細データ ---
with st.expander("📋 詳細データ表示", expanded=False):
    st.dataframe(filtered.head(200), use_container_width=True, height=400)

# --- レポート ---
if REPORT_PATH.exists():
    with st.expander("📄 分析レポートを表示", expanded=False):
        st.markdown(REPORT_PATH.read_text(encoding="utf-8"))

"""
app.py — 退学リスク早期警戒ダッシュボード（Streamlit）
起動: cd 09_education/01_dropout_risk && streamlit run app.py
"""
from pathlib import Path
import pandas as pd
import yaml
import streamlit as st

BASE = Path(__file__).resolve().parent
OUT  = BASE / "output"
CHARTS = OUT / "charts"

st.set_page_config(page_title="退学リスクダッシュボード", page_icon="🎓", layout="wide")

@st.cache_data
def load_data():
    csv_path = OUT / "cleaned_dropout_202401.csv"
    if not csv_path.exists():
        return None
    return pd.read_csv(csv_path, encoding="utf-8-sig")

@st.cache_data
def load_config():
    with open(BASE / "config.yml", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    config = load_config()
    high_thresh = config["high_risk_threshold"]
    med_thresh  = config["medium_risk_threshold"]
    low_att     = config["low_attendance_alert"]

    st.title("退学リスク早期警戒システム")
    st.caption("2024年1月末時点 | 200受講生 × 5科目")

    df = load_data()
    if df is None:
        st.error("データが見つかりません。cleanse.py を先に実行してください。")
        return

    # 受講生単位集計
    stu_df = df.groupby("student_id").agg(
        student_name=("student_name", "first"),
        course=("course", "first"),
        avg_score=("dropout_risk_score", "mean"),
        avg_attendance=("attendance_rate", "mean"),
        avg_midterm=("midterm_score", "mean"),
        avg_final=("final_score", "mean"),
    ).reset_index().round(1)

    def classify(score):
        if score < high_thresh: return "高リスク"
        elif score < med_thresh: return "中リスク"
        else: return "低リスク"

    stu_df["student_risk"] = stu_df["avg_score"].apply(classify)

    # フィルター
    col1, col2 = st.columns(2)
    with col1:
        all_courses = sorted(stu_df["course"].unique())
        selected_courses = st.multiselect("コースフィルター", all_courses, default=all_courses)
    with col2:
        risk_filter = st.selectbox("リスクフィルター", ["全受講生", "高リスクのみ", "中リスク以上"])

    filt_stu = stu_df[stu_df["course"].isin(selected_courses)]
    if risk_filter == "高リスクのみ":
        filt_stu = filt_stu[filt_stu["student_risk"] == "高リスク"]
    elif risk_filter == "中リスク以上":
        filt_stu = filt_stu[filt_stu["student_risk"].isin(["高リスク", "中リスク"])]

    # メトリクス
    st.divider()
    m1, m2, m3, m4, m5 = st.columns(5)
    n_high     = (filt_stu["student_risk"] == "高リスク").sum()
    n_mid      = (filt_stu["student_risk"] == "中リスク").sum()
    avg_score  = filt_stu["avg_score"].mean()
    low_att_n  = (filt_stu["avg_attendance"] < low_att).sum()

    m1.metric("総受講生数", f"{len(filt_stu)}名")
    m2.metric("高リスク", f"{n_high}名", delta=f"{n_high/max(len(filt_stu),1)*100:.1f}%", delta_color="inverse")
    m3.metric("中リスク", f"{n_mid}名")
    m4.metric("平均リスクスコア", f"{avg_score:.1f}点")
    m5.metric("低出席率", f"{low_att_n}名", delta=f"<{low_att:.0f}%", delta_color="inverse")

    st.divider()

    # チャートタブ
    tab1, tab2, tab3 = st.tabs(["リスク分布", "科目別スコア", "散布図"])

    chart1 = CHARTS / "bar_risk_distribution.png"
    chart2 = CHARTS / "bar_subject_avg_score.png"
    chart3 = CHARTS / "scatter_attendance_score.png"

    with tab1:
        if chart1.exists():
            st.image(str(chart1), use_container_width=True)
        else:
            st.info("visualize.py を実行してグラフを生成してください")

    with tab2:
        if chart2.exists():
            st.image(str(chart2), use_container_width=True)
        else:
            st.info("visualize.py を実行してグラフを生成してください")

    with tab3:
        if chart3.exists():
            st.image(str(chart3), use_container_width=True)
        else:
            st.info("visualize.py を実行してグラフを生成してください")

    st.divider()

    # アラート受講生テーブル
    st.subheader("アラート受講生（退学リスクスコア低位順）")
    alert_df = filt_stu.sort_values("avg_score").head(20)[
        ["student_id","student_name","course","student_risk","avg_score","avg_attendance","avg_midterm","avg_final"]
    ]
    alert_df.columns = ["受講生ID","氏名","コース","リスク分類","平均スコア","平均出席率","平均中間点","平均期末点"]

    def color_risk(val):
        if val == "高リスク": return "background-color: #fde8e8; color: #c0392b; font-weight: bold"
        elif val == "中リスク": return "background-color: #fef3cd; color: #e67e22"
        return ""

    styled = alert_df.style.map(color_risk, subset=["リスク分類"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # 分析レポート
    report_path = OUT / "analysis_report.md"
    if report_path.exists():
        with st.expander("分析レポート全文", expanded=False):
            st.markdown(report_path.read_text(encoding="utf-8"))

if __name__ == "__main__":
    main()

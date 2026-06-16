"""
app.py
医療・介護 シフト分析ダッシュボード（Streamlit）
"""

import os
import streamlit as st
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEANED_FILE = os.path.join(BASE_DIR, "output", "cleaned_shift_202401.csv")
SUMMARY_FILE = os.path.join(BASE_DIR, "output", "shift_summary_202401.csv")
REPORT_FILE = os.path.join(BASE_DIR, "output", "analysis_report.md")
CHARTS_DIR = os.path.join(BASE_DIR, "output", "charts")


@st.cache_data
def load_data():
    df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")
    summary = pd.read_csv(SUMMARY_FILE, encoding="utf-8-sig")
    return df, summary


def detect_consecutive_night(df: pd.DataFrame, threshold: int = 3) -> int:
    """連続夜勤希望者数を返す"""
    df = df.copy()
    df["date_dt"] = pd.to_datetime(df["date"])
    df = df.sort_values(["staff_id", "date_dt"])
    risk_count = 0
    for _, grp in df.groupby("staff_id"):
        run = 0
        for shift in grp["preferred_shift"]:
            if shift == "夜勤":
                run += 1
                if run >= threshold:
                    risk_count += 1
                    break
            else:
                run = 0
    return risk_count


def main():
    st.set_page_config(
        page_title="医療・介護 シフト分析ダッシュボード",
        page_icon="[HC]",
        layout="wide",
    )

    st.title("[HC] 医療・介護 シフト分析ダッシュボード")
    st.caption("対象期間: 2024年1月 ／ C-16 シフト希望・配置分析パイプライン")

    if not os.path.isfile(CLEANED_FILE):
        st.error("データが見つかりません。パイプラインを実行してください。")
        st.code("python _gen_sample_data.py && python cleanse.py && python analyze.py")
        return

    df, summary = load_data()

    # ── メトリクス ─────────────────────────────────────────────────────
    n_staff = df["staff_id"].nunique()
    n_night = int((df["preferred_shift"] == "夜勤").sum())
    avg_night_ratio = summary["night_ratio"].mean()
    risk_count = detect_consecutive_night(df, threshold=3)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("スタッフ総数", f"{n_staff}名")
    col2.metric("夜勤希望総数", f"{n_night}件")
    col3.metric("平均夜勤比率", f"{avg_night_ratio:.1%}")
    col4.metric("疲労リスク者数", f"{risk_count}名", delta=f"連続3日以上" if risk_count > 0 else "問題なし")

    st.divider()

    # ── フィルター ─────────────────────────────────────────────────────
    st.subheader("フィルター")
    roles = sorted(df["role"].dropna().unique().tolist())
    selected_roles = st.multiselect("役職フィルター", roles, default=roles)

    df_filtered = df[df["role"].isin(selected_roles)] if selected_roles else df
    summary_filtered = summary[summary["role"].isin(selected_roles)] if selected_roles else summary

    st.divider()

    # ── 夜勤希望ランキング ─────────────────────────────────────────────
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("[N] 夜勤希望ランキング（上位15名）")
        night_rank = (
            summary_filtered[["name", "role", "night_count", "night_ratio", "employment_type"]]
            .sort_values("night_count", ascending=False)
            .head(15)
            .reset_index(drop=True)
        )
        # employment_type を summary から補完
        if "employment_type" not in night_rank.columns:
            emp_map = df_filtered.drop_duplicates("staff_id").set_index("staff_id")["employment_type"]
            night_rank["employment_type"] = night_rank["name"].map(
                summary_filtered.set_index("name").get("staff_id", pd.Series(dtype=str))
            )
        night_rank.index += 1
        night_rank.columns = ["氏名", "役職", "夜勤回数", "夜勤比率", "雇用形態"]
        night_rank["夜勤比率"] = night_rank["夜勤比率"].map(lambda v: f"{v:.1%}")
        st.dataframe(night_rank, use_container_width=True)

    with col_right:
        st.subheader("📊 役職別 夜勤希望率")
        role_night = (
            df_filtered.groupby("role")["preferred_shift"]
            .apply(lambda s: (s == "夜勤").mean() * 100)
            .rename("夜勤希望率(%)")
            .reset_index()
        )
        st.bar_chart(role_night.set_index("role"))

    st.divider()

    # ── チャート表示 ──────────────────────────────────────────────────
    st.subheader("📈 チャート")
    chart_files = {
        "役職別夜勤希望率": os.path.join(CHARTS_DIR, "bar_role_night_ratio.png"),
        "夜勤希望回数上位15名": os.path.join(CHARTS_DIR, "bar_staff_night_count.png"),
        "施設別シフト分布": os.path.join(CHARTS_DIR, "stacked_shift_distribution.png"),
    }
    tabs = st.tabs(list(chart_files.keys()))
    for tab, (title, path) in zip(tabs, chart_files.items()):
        with tab:
            if os.path.isfile(path):
                st.image(path, use_container_width=True)
            else:
                st.warning(f"{path} が見つかりません。visualize.py を実行してください。")

    st.divider()

    # ── レポートテキスト ──────────────────────────────────────────────
    st.subheader("📄 分析レポート")
    if os.path.isfile(REPORT_FILE):
        with open(REPORT_FILE, encoding="utf-8") as f:
            report_text = f.read()
        with st.expander("レポートを表示", expanded=False):
            st.markdown(report_text)
    else:
        st.warning("analysis_report.md が見つかりません。analyze.py を実行してください。")

    # ── 詳細データ ────────────────────────────────────────────────────
    st.subheader("📋 スタッフサマリー")
    st.dataframe(summary_filtered.sort_values("night_count", ascending=False), use_container_width=True)


if __name__ == "__main__":
    main()

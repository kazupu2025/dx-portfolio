# -*- coding: utf-8 -*-
"""
B-77: 製造 設備稼働ログ 異常予兆検知ダッシュボード
Streamlit ダッシュボード
"""
import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUT = BASE_DIR / "output"


@st.cache_data
def load_mfg_equipment_log_data() -> pd.DataFrame:
    path = OUT / "anomaly_sensor_202401.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, encoding="utf-8-sig")
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    for col in ["temperature", "vibration", "pressure", "rpm", "max_z", "consecutive_alert"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


st.title("⚙️ B-77 製造 設備稼働ログ 異常予兆検知ダッシュボード")
st.caption("B-77 | 製造 × 設備管理 | 5台センサーデータ Zスコア異常予兆検知 | 2024年1月")

df_all = load_mfg_equipment_log_data()

if df_all.empty:
    st.error(f"センサーデータが見つかりません: {OUT / 'anomaly_sensor_202401.csv'}")
    st.info("先にパイプラインを実行してください。")
    st.stop()

# サイドバー
with st.sidebar:
    st.header("🔍 フィルター")
    equipment_ids = sorted(df_all["equipment_id"].dropna().unique().tolist()) if "equipment_id" in df_all.columns else []
    selected_eq = st.multiselect("設備フィルター", equipment_ids, default=equipment_ids, key="b77_equipment_filter")
    alert_levels = ["CRITICAL", "WARNING", "NORMAL"]
    selected_alert = st.multiselect("アラートレベル", alert_levels, default=alert_levels, key="b77_alert_filter")

filtered = df_all[df_all["equipment_id"].isin(selected_eq)].copy() if selected_eq and "equipment_id" in df_all.columns else df_all.copy()
if "alert_level" in filtered.columns and selected_alert:
    filtered = filtered[filtered["alert_level"].isin(selected_alert)]

op_df = filtered[filtered["is_operating"] == 1].copy() if "is_operating" in filtered.columns else filtered.copy()

n_critical = int((op_df["alert_level"] == "CRITICAL").sum()) if "alert_level" in op_df.columns else 0
n_warning = int((op_df["alert_level"] == "WARNING").sum()) if "alert_level" in op_df.columns else 0
precursor_eq = op_df[op_df["consecutive_alert"] >= 2]["equipment_id"].nunique() if "consecutive_alert" in op_df.columns and "equipment_id" in op_df.columns else 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("総計測数", f"{len(filtered):,}")
col2.metric("稼働中レコード数", f"{len(op_df):,}")
col3.metric("CRITICALアラート数", f"{n_critical:,}",
            delta="要対応" if n_critical > 0 else "正常",
            delta_color="inverse" if n_critical > 0 else "normal")
col4.metric("WARNINGアラート数", f"{n_warning:,}")
col5.metric("予兆検知設備数(≥2h)", f"{precursor_eq}")

st.divider()

tab1, tab2, tab3 = st.tabs(["🌡️ 温度トレンド", "🚨 アラート集計", "📋 アラートデータ"])

with tab1:
    st.subheader("設備別 平均温度")
    if "equipment_id" in filtered.columns and "temperature" in filtered.columns:
        temp_by_eq = filtered.groupby("equipment_id")["temperature"].mean().sort_values(ascending=True)
        st.bar_chart(temp_by_eq)

    st.subheader("時系列 温度トレンド（設備別平均）")
    if "timestamp" in filtered.columns and "temperature" in filtered.columns and "equipment_id" in filtered.columns:
        filtered_ts = filtered.dropna(subset=["timestamp"]).copy()
        filtered_ts["hour"] = filtered_ts["timestamp"].dt.floor("h")
        temp_trend = filtered_ts.groupby(["hour", "equipment_id"])["temperature"].mean().unstack(fill_value=None)
        if not temp_trend.empty:
            st.line_chart(temp_trend)

with tab2:
    st.subheader("設備別 アラート件数")
    if "equipment_id" in filtered.columns and "alert_level" in filtered.columns:
        alert_counts = filtered.groupby(["equipment_id", "alert_level"]).size().unstack(fill_value=0)
        st.bar_chart(alert_counts)

    st.subheader("設備別 最大Zスコア")
    if "equipment_id" in filtered.columns and "max_z" in filtered.columns:
        z_by_eq = filtered.groupby("equipment_id")["max_z"].max().sort_values(ascending=False)
        st.bar_chart(z_by_eq)

with tab3:
    st.subheader("アラートデータ（CRITICAL / WARNING）")
    if "alert_level" in filtered.columns:
        alert_table = filtered[filtered["alert_level"].isin(["CRITICAL", "WARNING"])]
        if "timestamp" in alert_table.columns:
            alert_table = alert_table.sort_values("timestamp", ascending=False)
        if not alert_table.empty:
            display_cols = [c for c in [
                "timestamp", "equipment_id", "equipment_name",
                "temperature", "vibration", "pressure", "rpm",
                "max_z", "alert_level", "consecutive_alert"
            ] if c in alert_table.columns]
            st.caption(f"件数: {len(alert_table):,} 件")
            st.dataframe(alert_table[display_cols].reset_index(drop=True), use_container_width=True, hide_index=True)
        else:
            st.info("選択フィルターにアラート該当なし")
    else:
        st.info("alert_level 列が見つかりません")

st.divider()
report_path = OUT / "analysis_report.md"
if report_path.exists():
    with st.expander("📄 分析レポートを表示", expanded=False):
        st.markdown(report_path.read_text(encoding="utf-8"))

"""
B-09 設備稼働ログ異常予兆検知 Streamlitダッシュボード
Usage: cd 02_manufacturing/02_equipment_log && streamlit run app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).parent
OUT  = BASE / "output"
CHARTS = OUT / "charts"

st.set_page_config(page_title="B-09 設備稼働ログ 異常予兆検知", layout="wide")
st.title("B-09 製造×設備稼働ログ 異常予兆検知")
st.markdown("5台の製造設備センサーデータからローリングZスコアによる異常予兆を検知します。")

@st.cache_data
def load_data():
    path = OUT / "anomaly_sensor_202401.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

df = load_data()

if df.empty:
    st.error("anomaly_sensor_202401.csv が見つかりません。`python output/analyze.py` を先に実行してください。")
    st.stop()

# サイドバーフィルター
st.sidebar.header("フィルター")
equipment_ids = sorted(df["equipment_id"].unique().tolist())
selected_eq = st.sidebar.multiselect("設備フィルター", equipment_ids, default=equipment_ids)
alert_levels = ["CRITICAL", "WARNING", "NORMAL"]
selected_alert = st.sidebar.multiselect("アラートレベル", alert_levels, default=alert_levels)

filtered = df[df["equipment_id"].isin(selected_eq)]
if "alert_level" in filtered.columns:
    filtered = filtered[filtered["alert_level"].isin(selected_alert)]

# メトリクス
op_df = filtered[filtered["is_operating"] == 1] if "is_operating" in filtered.columns else filtered

if "alert_level" in op_df.columns:
    n_critical = (op_df["alert_level"] == "CRITICAL").sum()
    n_warning  = (op_df["alert_level"] == "WARNING").sum()
else:
    n_critical = n_warning = 0

if "consecutive_alert" in op_df.columns:
    precursor_eq = op_df[op_df["consecutive_alert"] >= 2]["equipment_id"].nunique()
else:
    precursor_eq = 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("総計測数", f"{len(filtered):,}")
col2.metric("稼働中レコード数", f"{len(op_df):,}")
col3.metric("CRITICALアラート数", f"{n_critical:,}", delta=None)
col4.metric("WARNINGアラート数", f"{n_warning:,}")
col5.metric("予兆検知設備数(≥2h)", f"{precursor_eq}")

st.divider()

# 3タブ
tab1, tab2, tab3 = st.tabs(["温度トレンド", "アラート集計", "センサーZスコアヒートマップ"])

with tab1:
    chart_path = CHARTS / "line_equipment_temperature.png"
    if chart_path.exists():
        st.image(str(chart_path), use_container_width=True)
    else:
        st.warning("グラフ未生成。`python output/visualize.py` を実行してください。")

with tab2:
    chart_path = CHARTS / "bar_equipment_alert_count.png"
    if chart_path.exists():
        st.image(str(chart_path), use_container_width=True)
    else:
        st.warning("グラフ未生成。`python output/visualize.py` を実行してください。")

with tab3:
    chart_path = CHARTS / "heatmap_equipment_sensor_z.png"
    if chart_path.exists():
        st.image(str(chart_path), use_container_width=True)
    else:
        st.warning("グラフ未生成。`python output/visualize.py` を実行してください。")

st.divider()

# アラートデータテーブル
st.subheader("アラートデータ（CRITICAL / WARNING）")
if "alert_level" in filtered.columns:
    alert_table = filtered[filtered["alert_level"].isin(["CRITICAL", "WARNING"])].sort_values("timestamp", ascending=False)
    if not alert_table.empty:
        display_cols = [c for c in ["timestamp", "equipment_id", "equipment_name",
                                     "temperature", "vibration", "pressure", "rpm",
                                     "max_z", "alert_level", "consecutive_alert"] if c in alert_table.columns]
        st.dataframe(alert_table[display_cols].reset_index(drop=True), use_container_width=True)
    else:
        st.info("選択フィルターにアラート該当なし")
else:
    st.info("alert_level 列が見つかりません")

# 分析レポートエキスパンダー
report_path = OUT / "analysis_report.md"
if report_path.exists():
    with st.expander("分析レポートを表示", expanded=False):
        with open(report_path, encoding="utf-8") as f:
            st.markdown(f.read())

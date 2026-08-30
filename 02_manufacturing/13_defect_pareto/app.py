# -*- coding: utf-8 -*-
"""
B-83: 製造 不良モード別パレート × 時系列複合分析ダッシュボード
Streamlit ダッシュボード（ローカルモジュール依存を排除したスタンドアロン版）
"""
from __future__ import annotations
import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path

try:
    import plotly.express as px
    import plotly.graph_objects as go
    _HAS_PLOTLY = True
except ImportError:
    _HAS_PLOTLY = False

BASE_DIR = Path(__file__).resolve().parent


# ── パレート分析ロジック（インライン） ──────────────────────────────
def run_pareto_analysis(df: pd.DataFrame, date_col: str, mode_col: str, count_col: str) -> dict:
    df = df.copy()
    df[count_col] = pd.to_numeric(df[count_col], errors="coerce").fillna(0)

    # パレート集計
    pareto = df.groupby(mode_col)[count_col].sum().sort_values(ascending=False).reset_index()
    pareto.columns = [mode_col, "count"]
    total = pareto["count"].sum()
    pareto["pct"] = pareto["count"] / total * 100
    pareto["cumulative_pct"] = pareto["pct"].cumsum()
    vital_few = pareto[pareto["cumulative_pct"] <= 80][mode_col].tolist()
    if not vital_few:
        vital_few = [pareto.iloc[0][mode_col]]

    # トレンド集計
    trend = df.groupby([date_col, mode_col])[count_col].sum().reset_index()

    # 月次集計
    monthly = df.groupby(date_col)[count_col].sum().reset_index()
    monthly = monthly.sort_values(date_col)

    top_mode = pareto.iloc[0][mode_col]
    top_mode_pct = float(pareto.iloc[0]["pct"])
    latest_month = str(monthly.iloc[-1][date_col]) if len(monthly) >= 1 else ""
    latest_total = int(monthly.iloc[-1][count_col]) if len(monthly) >= 1 else 0
    prev_total = int(monthly.iloc[-2][count_col]) if len(monthly) >= 2 else latest_total

    if latest_total < prev_total:
        verdict = "good"
    elif latest_total == prev_total:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "pareto_df": pareto,
        "trend_df": trend,
        "monthly_df": monthly,
        "vital_few": vital_few,
        "top_mode": top_mode,
        "top_mode_pct": top_mode_pct,
        "total_count": int(total),
        "latest_month": latest_month,
        "latest_total": latest_total,
        "prev_total": prev_total,
        "verdict": verdict,
        "mode_col": mode_col,
        "date_col": date_col,
        "count_col": count_col,
    }


def generate_sample_df() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    modes = ["傷", "欠け", "汚れ", "寸法NG", "外観NG"]
    months = ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]
    rows = []
    for m in months:
        for mode in modes:
            rows.append({"yearmonth": m, "defect_mode": mode,
                         "count": int(rng.integers(5, 50))})
    return pd.DataFrame(rows)


# ── UI ─────────────────────────────────────────────────────────────
st.title("📊 B-83 製造 不良モード別パレート × 時系列複合分析")
st.caption("B-83 | 製造 × 品質管理 | パレート分析 + 不良モード別月次トレンド")

for key, val in [("b83_df", None), ("b83_result", None)]:
    if key not in st.session_state:
        st.session_state[key] = val

with st.sidebar:
    st.header("⚙ 設定")
    if st.button("サンプルデータを使用", use_container_width=True, key="b83_sample"):
        st.session_state.b83_df = generate_sample_df()
    uploaded = st.file_uploader("CSVアップロード", type=["csv"], key="b83_upload")
    if uploaded:
        try:
            st.session_state.b83_df = pd.read_csv(uploaded, encoding="utf-8-sig")
        except UnicodeDecodeError:
            st.session_state.b83_df = pd.read_csv(uploaded, encoding="shift_jis")

    df = st.session_state.b83_df
    date_col = mode_col = count_col = None
    run_btn = False

    if df is not None:
        cols = df.columns.tolist()
        date_col = st.selectbox("年月列", cols, key="b83_date")
        mode_col = st.selectbox("不良モード列", cols, index=min(1, len(cols)-1), key="b83_mode")
        count_col = st.selectbox("件数列", cols, index=min(2, len(cols)-1), key="b83_count")
        run_btn = st.button("▶ 分析実行", type="primary", use_container_width=True, key="b83_run")

df = st.session_state.b83_df
if df is None:
    st.info("サイドバーから CSV をアップロードするか、「サンプルデータを使用」をクリックしてください。")
    st.stop()

if run_btn:
    try:
        st.session_state.b83_result = run_pareto_analysis(df, date_col, mode_col, count_col)
    except Exception as e:
        st.error(str(e))

result = st.session_state.b83_result
if result is None:
    st.info("サイドバーで設定を選択し、「▶ 分析実行」を押してください。")
    st.stop()

# KPI
_COLOR = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_LABEL = {"good": "✅ 改善中", "warning": "⚠️ 横ばい", "alert": "❌ 悪化"}
verdict = result["verdict"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("全期間合計件数", f"{result['total_count']:,}件")
c2.metric("最多不良モード", f"{result['top_mode']}（{result['top_mode_pct']:.1f}%）")
c3.metric("vital few", f"{len(result['vital_few'])}モードで80%超")
c4.metric("最新月トレンド", _LABEL[verdict],
          delta=f"{result['latest_total']}件（前月{result['prev_total']}件）",
          delta_color="normal" if verdict == "good" else "inverse")

st.divider()

pareto_df = result["pareto_df"]
mc = result["mode_col"]
trend_df = result["trend_df"]
monthly_df = result["monthly_df"]
dc = result["date_col"]
cc = result["count_col"]

if _HAS_PLOTLY:
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("パレート図")
        fig = go.Figure()
        colors = ["#ef4444" if m in result["vital_few"] else "#3b82f6"
                  for m in pareto_df[mc]]
        fig.add_bar(x=pareto_df[mc], y=pareto_df["count"], marker_color=colors, name="件数")
        fig.add_scatter(x=pareto_df[mc], y=pareto_df["cumulative_pct"],
                        mode="lines+markers", name="累積%", yaxis="y2",
                        line=dict(color="#f59e0b", width=2))
        fig.add_hline(y=80, line_dash="dash", line_color="orange", yref="y2",
                      annotation_text="80%", annotation_position="top right")
        fig.update_layout(
            yaxis2=dict(overlaying="y", side="right", range=[0, 110], title="累積%"),
            yaxis=dict(title="件数"),
            showlegend=True, height=380,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.subheader("不良モード別 月次トレンド")
        pivot = trend_df.pivot_table(index=dc, columns=mc, values=cc, aggfunc="sum", fill_value=0)
        fig2 = px.line(pivot, markers=True, title="月次不良件数推移")
        fig2.update_layout(xaxis_title="年月", yaxis_title="件数", height=380)
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.subheader("パレート集計（Plotly未インストール）")
    st.bar_chart(pareto_df.set_index(mc)["count"].sort_values(ascending=False))
    st.subheader("月次トレンド")
    pivot = trend_df.pivot_table(index=dc, columns=mc, values=cc, aggfunc="sum", fill_value=0)
    st.line_chart(pivot)

st.subheader("パレート集計テーブル")
display_df = pareto_df.copy()
display_df["cumulative_pct"] = display_df["cumulative_pct"].map(lambda x: f"{x:.1f}%")
display_df["pct"] = display_df["pct"].map(lambda x: f"{x:.1f}%")
display_df["vital_few"] = display_df[mc].apply(
    lambda m: "★" if m in result["vital_few"] else ""
)
st.dataframe(display_df, hide_index=True, use_container_width=True)

st.subheader("月次合計推移")
st.bar_chart(monthly_df.set_index(dc)[cc])

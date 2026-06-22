"""出荷検査合否率・保留件数レポート — Plotly チャート。"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

_BG    = "#f5f7fa"
_BLUE  = "#1e3a5f"
_TEAL  = "#0891b2"
_GREEN = "#16a34a"
_RED   = "#dc2626"
_AMBER = "#d97706"

def pass_rate_chart(result_df: pd.DataFrame) -> go.Figure:
    """合格率 月次折れ線グラフ。"""
    months = sorted(result_df["month"].unique())
    monthly = result_df.groupby("month")[["inspected","passed","hold_count"]].sum().reindex(months)
    pass_rates = (monthly["passed"] / monthly["inspected"] * 100).tolist()
    hold_rates = (monthly["hold_count"] / monthly["inspected"] * 100).tolist()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=months, y=pass_rates, mode="lines+markers",
                             name="合格率", line=dict(color=_BLUE, width=2), marker=dict(size=8)))
    fig.add_trace(go.Scatter(x=months, y=hold_rates, mode="lines+markers",
                             name="保留率", line=dict(color=_AMBER, width=2, dash="dot"), marker=dict(size=8)))
    fig.add_hline(y=99.0, line_dash="dash", line_color=_GREEN,
                  annotation_text="99%（good）", annotation_position="right")
    fig.add_hline(y=95.0, line_dash="dash", line_color=_RED,
                  annotation_text="95%（alert）", annotation_position="right")
    fig.update_layout(title="出荷検査 合格率・保留率 月次推移",
                      xaxis_title="年月", yaxis=dict(title="率（%）", range=[85, 101]),
                      height=380, plot_bgcolor=_BG, paper_bgcolor=_BG,
                      legend=dict(orientation="h", y=-0.25))
    return fig

def monthly_bar_chart(result_df: pd.DataFrame) -> go.Figure:
    """月次検査件数 積み上げ棒グラフ（合格 / 保留 / その他）。"""
    months = sorted(result_df["month"].unique())
    monthly = result_df.groupby("month")[["inspected","passed","hold_count"]].sum().reindex(months)
    passed   = monthly["passed"].tolist()
    hold     = monthly["hold_count"].tolist()
    failed   = (monthly["inspected"] - monthly["passed"] - monthly["hold_count"]).clip(lower=0).tolist()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=months, y=passed, name="合格", marker_color=_GREEN))
    fig.add_trace(go.Bar(x=months, y=hold, name="保留", marker_color=_AMBER))
    fig.add_trace(go.Bar(x=months, y=failed, name="不合格", marker_color=_RED))
    fig.update_layout(barmode="stack", title="月次 出荷検査件数（合格 / 保留 / 不合格）",
                      xaxis_title="年月", yaxis_title="件数（件）",
                      height=320, plot_bgcolor=_BG, paper_bgcolor=_BG,
                      legend=dict(orientation="h", y=-0.25))
    return fig

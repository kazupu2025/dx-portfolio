"""CAPA 完了率・期限遵守率レポート — Plotly チャート。"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

_BG    = "#f5f7fa"
_BLUE  = "#1e3a5f"
_TEAL  = "#0891b2"
_GREEN = "#16a34a"
_RED   = "#dc2626"


def rate_trend_chart(result_df: pd.DataFrame) -> go.Figure:
    """完了率 + 期限遵守率 月次折れ線グラフ。

    result_df must contain columns: month, total, completed, on_time_completed.
    """
    months = sorted(result_df["month"].unique())
    monthly = (
        result_df.groupby("month")[["total", "completed", "on_time_completed"]]
        .sum()
        .reindex(months)
    )
    comp_rates   = (monthly["completed"]        / monthly["total"] * 100).tolist()
    ontime_rates = (monthly["on_time_completed"] / monthly["total"] * 100).tolist()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months, y=comp_rates, mode="lines+markers",
        name="完了率", line=dict(color=_BLUE, width=2),
        marker=dict(size=8),
    ))
    fig.add_trace(go.Scatter(
        x=months, y=ontime_rates, mode="lines+markers",
        name="期限遵守率", line=dict(color=_TEAL, width=2, dash="dot"),
        marker=dict(size=8),
    ))
    fig.add_hline(y=90.0, line_dash="dash", line_color=_GREEN,
                  annotation_text="90%（good）", annotation_position="right")
    fig.add_hline(y=70.0, line_dash="dash", line_color=_RED,
                  annotation_text="70%（alert）", annotation_position="right")
    fig.update_layout(
        title="CAPA 完了率・期限遵守率 月次推移",
        xaxis_title="年月",
        yaxis=dict(title="率（%）", range=[0, 105]),
        height=380,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25),
    )
    return fig


def monthly_bar_chart(result_df: pd.DataFrame) -> go.Figure:
    """月次 CAPA 件数 積み上げ棒グラフ（完了 / 未完了）。

    result_df must contain columns: month, total, completed.
    """
    months = sorted(result_df["month"].unique())
    monthly = (
        result_df.groupby("month")[["total", "completed"]]
        .sum()
        .reindex(months)
    )
    completed = monthly["completed"].tolist()
    open_cnt  = (monthly["total"] - monthly["completed"]).tolist()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=months, y=completed, name="完了",
        marker_color=_GREEN,
    ))
    fig.add_trace(go.Bar(
        x=months, y=open_cnt, name="未完了",
        marker_color=_RED,
    ))
    fig.update_layout(
        barmode="stack",
        title="月次 CAPA 件数（完了 / 未完了）",
        xaxis_title="年月",
        yaxis_title="件数（件）",
        height=320,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25),
    )
    return fig

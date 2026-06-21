"""品質コストROI分析 — Plotly チャート。"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

_NAVY  = "#1e3a5f"
_GREEN = "#16a34a"
_RED   = "#dc2626"
_AMBER = "#d97706"
_BG    = "#f5f7fa"


def cost_bar_chart(df: pd.DataFrame) -> go.Figure:
    months = df["month"].tolist()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=months, y=df["prevention_cost"],
        name="予防コスト", marker_color=_GREEN,
    ))
    fig.add_trace(go.Bar(
        x=months, y=df["appraisal_cost"],
        name="評価コスト", marker_color=_NAVY,
    ))
    fig.add_trace(go.Bar(
        x=months, y=df["failure_cost"],
        name="失敗コスト", marker_color=_RED,
    ))
    fig.update_layout(
        barmode="stack",
        title="月別 品質コスト構成（PAF）",
        xaxis_title="月",
        yaxis_title="金額（円）",
        height=380,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25),
    )
    return fig


def roi_line_chart(df: pd.DataFrame, roi_series: list[float]) -> go.Figure:
    months = df["month"].tolist()[1:]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months, y=roi_series,
        mode="lines+markers",
        name="ROI",
        line=dict(color=_AMBER, width=2),
        marker=dict(size=7),
    ))
    fig.add_hline(
        y=1.0,
        line_dash="dash",
        line_color=_NAVY,
        annotation_text="ROI=1.0（損益分岐点）",
        annotation_position="top right",
    )
    fig.update_layout(
        title="月次 ROI 推移",
        xaxis_title="月",
        yaxis_title="ROI",
        height=320,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
    )
    return fig

"""特採件数・理由別集計・月次推移 — Plotly チャート。"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

_NAVY   = "#1e3a5f"
_GREEN  = "#16a34a"
_RED    = "#dc2626"
_BG     = "#f5f7fa"

_PALETTE = [
    "#1e3a5f", "#16a34a", "#d97706", "#dc2626",
    "#7c3aed", "#0891b2", "#be185d", "#65a30d",
]


def trend_chart(result_df: pd.DataFrame) -> go.Figure:
    """理由別 月次件数 積み上げ棒グラフ。

    result_df must contain columns: month, reason, count.
    """
    months  = sorted(result_df["month"].unique())
    reasons = sorted(result_df["reason"].unique())

    pivot = (
        result_df.groupby(["month", "reason"])["count"]
        .sum()
        .reset_index()
        .pivot(index="month", columns="reason", values="count")
        .reindex(months)
        .fillna(0)
    )

    fig = go.Figure()
    for i, reason in enumerate(reasons):
        if reason not in pivot.columns:
            continue
        fig.add_trace(go.Bar(
            x=months,
            y=pivot[reason].tolist(),
            name=reason,
            marker_color=_PALETTE[i % len(_PALETTE)],
        ))

    fig.add_hline(y=10.0, line_dash="dash", line_color=_RED,
                  annotation_text="10件（alert）", annotation_position="right")
    fig.add_hline(y=3.0, line_dash="dash", line_color=_GREEN,
                  annotation_text="3件（good）", annotation_position="right")
    fig.update_layout(
        barmode="stack",
        title="特採件数 月次推移（理由別）",
        xaxis_title="年月",
        yaxis_title="特採件数（件）",
        height=380,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25),
    )
    return fig


def reason_bar_chart(result_df: pd.DataFrame) -> go.Figure:
    """理由別 総特採件数 横棒グラフ（降順）。

    result_df must contain columns: reason, count.
    """
    reason_totals = (
        result_df.groupby("reason")["count"]
        .sum()
        .sort_values(ascending=True)
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=reason_totals.values,
        y=reason_totals.index,
        orientation="h",
        marker_color=_NAVY,
        text=[f"{int(v)}件" for v in reason_totals.values],
        textposition="outside",
    ))
    fig.update_layout(
        title="理由別 特採件数",
        xaxis=dict(title="件数（件）", range=[0, None]),
        yaxis_title="理由",
        height=320,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        showlegend=False,
    )
    return fig

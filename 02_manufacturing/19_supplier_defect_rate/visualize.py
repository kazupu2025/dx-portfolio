"""協力会社別受入不良率月報 — Plotly チャート。"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

_NAVY   = "#1e3a5f"
_GREEN  = "#16a34a"
_AMBER  = "#d97706"
_RED    = "#dc2626"
_BG     = "#f5f7fa"

_PALETTE = [
    "#1e3a5f", "#16a34a", "#d97706", "#dc2626",
    "#7c3aed", "#0891b2", "#be185d", "#65a30d",
]

_VERDICT_COLOR = {"good": _GREEN, "warning": _AMBER, "alert": _RED}


def defect_rate_chart(result_df: pd.DataFrame) -> go.Figure:
    """協力会社 × 月ごとの不良率グループ棒グラフ。"""
    suppliers = sorted(result_df["supplier"].unique())
    months    = sorted(result_df["month"].unique())

    fig = go.Figure()
    for i, sup in enumerate(suppliers):
        sub = result_df[result_df["supplier"] == sup]
        month_rate = {row["month"]: row["defect_rate"]
                      for _, row in sub.iterrows()}
        rates = [month_rate.get(m, None) for m in months]
        fig.add_trace(go.Bar(
            x=months, y=rates,
            name=sup,
            marker_color=_PALETTE[i % len(_PALETTE)],
        ))

    fig.add_hline(y=3.0, line_dash="dash", line_color=_RED,
                  annotation_text="3.0%（alert）", annotation_position="right")
    fig.add_hline(y=1.0, line_dash="dash", line_color=_GREEN,
                  annotation_text="1.0%（good）", annotation_position="right")
    fig.update_layout(
        barmode="group",
        title="協力会社別 月次不良率推移",
        xaxis_title="年月",
        yaxis_title="不良率（%）",
        height=380,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25),
    )
    return fig


def supplier_bar_chart(result_df: pd.DataFrame) -> go.Figure:
    """協力会社別 加重平均不良率横棒グラフ（verdict 色分け）。"""
    supplier_stats = result_df.groupby("supplier")[
        ["defect_qty", "incoming_qty"]
    ].sum()
    supplier_rates = (
        supplier_stats["defect_qty"] / supplier_stats["incoming_qty"] * 100.0
    ).sort_values(ascending=True)

    colors = [
        _GREEN if v <= 1.0 else _AMBER if v <= 3.0 else _RED
        for v in supplier_rates
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=supplier_rates.values,
        y=supplier_rates.index,
        orientation="h",
        marker_color=colors,
        text=[f"{v:.2f}%" for v in supplier_rates.values],
        textposition="outside",
    ))
    fig.add_vline(x=1.0, line_dash="dash", line_color=_GREEN,
                  annotation_text="1.0%", annotation_position="top")
    fig.add_vline(x=3.0, line_dash="dash", line_color=_RED,
                  annotation_text="3.0%", annotation_position="top")
    fig.update_layout(
        title="協力会社別 平均不良率",
        xaxis=dict(title="平均不良率（%）", range=[0, None]),
        yaxis_title="協力会社",
        height=320,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        showlegend=False,
    )
    return fig

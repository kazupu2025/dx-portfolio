"""顧客クレーム件数・原因分類 月次集計 — Plotly チャート。"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

_NAVY  = "#1e3a5f"
_GREEN = "#16a34a"
_AMBER = "#d97706"
_RED   = "#dc2626"
_BG    = "#f5f7fa"

_PALETTE = [
    "#1e3a5f", "#16a34a", "#d97706", "#dc2626",
    "#7c3aed", "#0891b2", "#be185d", "#65a30d",
]


def claim_trend_chart(result_df: pd.DataFrame) -> go.Figure:
    """顧客 × 月ごとのクレーム件数グループ棒グラフ。

    result_df must contain columns: customer, month, count.
    """
    customers = sorted(result_df["customer"].unique())
    months    = sorted(result_df["month"].unique())

    pivot = (
        result_df.groupby(["customer", "month"])["count"]
        .sum()
        .reset_index()
        .pivot(index="month", columns="customer", values="count")
        .reindex(months)
    )

    fig = go.Figure()
    for i, cust in enumerate(customers):
        fig.add_trace(go.Bar(
            x=months,
            y=pivot[cust].tolist() if cust in pivot.columns else [None] * len(months),
            name=cust,
            marker_color=_PALETTE[i % len(_PALETTE)],
        ))

    fig.add_hline(y=15.0, line_dash="dash", line_color=_RED,
                  annotation_text="15件（alert）", annotation_position="right")
    fig.add_hline(y=5.0, line_dash="dash", line_color=_GREEN,
                  annotation_text="5件（good）", annotation_position="right")
    fig.update_layout(
        barmode="group",
        title="顧客別 月次クレーム件数推移",
        xaxis_title="年月",
        yaxis_title="クレーム件数（件）",
        height=380,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25),
    )
    return fig


def category_chart(result_df: pd.DataFrame) -> go.Figure:
    """原因分類別 総クレーム件数 横棒グラフ（件数降順）。

    result_df must contain columns: category, count.
    """
    cat_totals = (
        result_df.groupby("category")["count"]
        .sum()
        .sort_values(ascending=True)
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=cat_totals.values,
        y=cat_totals.index,
        orientation="h",
        marker_color=_NAVY,
        text=[f"{int(v)}件" for v in cat_totals.values],
        textposition="outside",
    ))
    fig.update_layout(
        title="原因分類別 クレーム件数",
        xaxis=dict(title="クレーム件数（件）", range=[0, None]),
        yaxis_title="原因分類",
        height=320,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        showlegend=False,
    )
    return fig

"""なぜなぜ分析 原因カテゴリ別集計・再発率トレンド — Plotly チャート。"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

_BG     = "#f5f7fa"
_NAVY   = "#1e3a5f"
_GREEN  = "#16a34a"
_RED    = "#dc2626"
_AMBER  = "#d97706"
_PALETTE = ["#1e3a5f","#16a34a","#d97706","#dc2626","#7c3aed","#0891b2"]

def recurrence_rate_chart(result_df: pd.DataFrame) -> go.Figure:
    """月次 再発率 + 件数 折れ線グラフ（2軸）。"""
    months = sorted(result_df["month"].unique())
    monthly = result_df.groupby("month")[["count","recurrence"]].sum().reindex(months)
    rates   = (monthly["recurrence"] / monthly["count"] * 100).tolist()
    counts  = monthly["count"].tolist()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=months, y=rates, mode="lines+markers", name="再発率(%)",
                             line=dict(color=_RED, width=2), marker=dict(size=8),
                             yaxis="y1"))
    fig.add_trace(go.Bar(x=months, y=counts, name="件数", marker_color=_NAVY,
                         opacity=0.3, yaxis="y2"))
    fig.add_hline(y=30.0, line_dash="dash", line_color=_RED,
                  annotation_text="30%（alert）", annotation_position="right")
    fig.add_hline(y=10.0, line_dash="dash", line_color=_GREEN,
                  annotation_text="10%（good）", annotation_position="right")
    fig.update_layout(
        title="なぜなぜ分析 再発率 月次推移",
        xaxis_title="年月",
        yaxis=dict(title="再発率（%）", range=[0, None], side="left"),
        yaxis2=dict(title="件数（件）", overlaying="y", side="right", showgrid=False),
        height=380, plot_bgcolor=_BG, paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25)
    )
    return fig

def category_bar_chart(result_df: pd.DataFrame) -> go.Figure:
    """原因カテゴリ別 件数 + 再発件数 横棒グラフ。"""
    cat_stats = result_df.groupby("cause_category")[["count","recurrence"]].sum().sort_values("count", ascending=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=cat_stats["count"].values, y=cat_stats.index, orientation="h",
                         name="件数", marker_color=_NAVY))
    fig.add_trace(go.Bar(x=cat_stats["recurrence"].values, y=cat_stats.index, orientation="h",
                         name="再発件数", marker_color=_RED))
    fig.update_layout(barmode="overlay", title="原因カテゴリ別 件数 / 再発件数",
                      xaxis=dict(title="件数", range=[0,None]),
                      yaxis_title="原因カテゴリ",
                      height=300, plot_bgcolor=_BG, paper_bgcolor=_BG,
                      legend=dict(orientation="h", y=-0.25))
    return fig

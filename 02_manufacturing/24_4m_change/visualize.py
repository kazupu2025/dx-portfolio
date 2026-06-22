"""4M変更台帳 集計・変更種別推移 — Plotly チャート。"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

_NAVY  = "#1e3a5f"
_GREEN = "#16a34a"
_RED   = "#dc2626"
_BG    = "#f5f7fa"
_PALETTE = ["#1e3a5f","#16a34a","#d97706","#dc2626","#7c3aed","#0891b2"]

def trend_chart(result_df: pd.DataFrame) -> go.Figure:
    """変更種別 月次件数 積み上げ棒グラフ。"""
    months = sorted(result_df["month"].unique())
    types  = sorted(result_df["change_type"].unique())
    pivot = (
        result_df.groupby(["month","change_type"])["count"].sum()
        .reset_index().pivot(index="month", columns="change_type", values="count")
        .reindex(months).fillna(0)
    )
    fig = go.Figure()
    for i, ct in enumerate(types):
        if ct not in pivot.columns:
            continue
        fig.add_trace(go.Bar(x=months, y=pivot[ct].tolist(), name=ct,
                             marker_color=_PALETTE[i % len(_PALETTE)]))
    fig.add_hline(y=15.0, line_dash="dash", line_color=_RED,
                  annotation_text="15件（alert）", annotation_position="right")
    fig.add_hline(y=5.0, line_dash="dash", line_color=_GREEN,
                  annotation_text="5件（good）", annotation_position="right")
    fig.update_layout(barmode="stack", title="4M変更件数 月次推移（変更種別）",
                      xaxis_title="年月", yaxis_title="変更件数（件）",
                      height=380, plot_bgcolor=_BG, paper_bgcolor=_BG,
                      legend=dict(orientation="h", y=-0.25))
    return fig

def type_bar_chart(result_df: pd.DataFrame) -> go.Figure:
    """変更種別 総件数 横棒グラフ（降順）。"""
    totals = result_df.groupby("change_type")["count"].sum().sort_values(ascending=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=totals.values, y=totals.index, orientation="h",
                         marker_color=_NAVY,
                         text=[f"{int(v)}件" for v in totals.values],
                         textposition="outside"))
    fig.update_layout(title="変更種別 件数", xaxis=dict(title="件数", range=[0,None]),
                      yaxis_title="変更種別", height=320,
                      plot_bgcolor=_BG, paper_bgcolor=_BG, showlegend=False)
    return fig

"""工程別不良コード頻度・月次トレンド — Plotly チャート。"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

_BG     = "#f5f7fa"
_NAVY   = "#1e3a5f"
_GREEN  = "#16a34a"
_RED    = "#dc2626"
_PALETTE = ["#1e3a5f","#16a34a","#d97706","#dc2626","#7c3aed","#0891b2","#be185d","#65a30d"]

def process_trend_chart(result_df: pd.DataFrame) -> go.Figure:
    """工程別 月次不良件数 積み上げ棒グラフ。"""
    months   = sorted(result_df["month"].unique())
    processes = sorted(result_df["process"].unique())
    pivot = (
        result_df.groupby(["month","process"])["count"].sum()
        .reset_index().pivot(index="month", columns="process", values="count")
        .reindex(months).fillna(0)
    )
    fig = go.Figure()
    for i, proc in enumerate(processes):
        if proc not in pivot.columns:
            continue
        fig.add_trace(go.Bar(x=months, y=pivot[proc].tolist(), name=proc,
                             marker_color=_PALETTE[i % len(_PALETTE)]))
    fig.add_hline(y=30.0, line_dash="dash", line_color=_RED,
                  annotation_text="30件（alert）", annotation_position="right")
    fig.add_hline(y=10.0, line_dash="dash", line_color=_GREEN,
                  annotation_text="10件（good）", annotation_position="right")
    fig.update_layout(barmode="stack", title="工程別 不良件数 月次推移",
                      xaxis_title="年月", yaxis_title="不良件数（件）",
                      height=380, plot_bgcolor=_BG, paper_bgcolor=_BG,
                      legend=dict(orientation="h", y=-0.25))
    return fig

def defect_code_bar_chart(result_df: pd.DataFrame) -> go.Figure:
    """不良コード別 総件数 横棒グラフ（降順）。"""
    totals = result_df.groupby("defect_code")["count"].sum().sort_values(ascending=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=totals.values, y=totals.index, orientation="h",
                         marker_color=_NAVY,
                         text=[f"{int(v)}件" for v in totals.values],
                         textposition="outside"))
    fig.update_layout(title="不良コード別 件数",
                      xaxis=dict(title="件数", range=[0,None]),
                      yaxis_title="不良コード",
                      height=300, plot_bgcolor=_BG, paper_bgcolor=_BG, showlegend=False)
    return fig

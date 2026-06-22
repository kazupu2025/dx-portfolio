"""4M変更前後品質比較 — Plotly チャート。"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

_BG    = "#f5f7fa"
_NAVY  = "#1e3a5f"
_GREEN = "#16a34a"
_RED   = "#dc2626"
_AMBER = "#d97706"
_TEAL  = "#0891b2"


def pvalue_bar_chart(result_summary: pd.DataFrame) -> go.Figure:
    """変更別 p値棒グラフ（p=0.05 基準線付き）。"""
    names = result_summary["change_name"].tolist()
    pvals = result_summary["p_value_t"].tolist()
    colors = [_GREEN if p < 0.05 else _AMBER for p in pvals]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=names, y=pvals, marker_color=colors,
        text=[f"{p:.4f}" for p in pvals], textposition="outside",
        name="p値（t検定）",
    ))
    fig.add_hline(y=0.05, line_dash="dash", line_color=_RED,
                  annotation_text="p=0.05（有意水準）", annotation_position="right")
    fig.update_layout(
        title="変更別 有意差検定 p値（p<0.05 で有意差あり）",
        xaxis_title="変更名称", yaxis=dict(title="p値", range=[0, 1.1]),
        height=360, plot_bgcolor=_BG, paper_bgcolor=_BG, showlegend=False,
    )
    return fig


def mean_comparison_chart(result_df: pd.DataFrame, result_summary: pd.DataFrame) -> go.Figure:
    """変更前後 平均値比較 グループ棒グラフ。"""
    names   = result_summary["change_name"].tolist()
    means_b = result_summary["mean_before"].tolist()
    means_a = result_summary["mean_after"].tolist()

    fig = go.Figure()
    fig.add_trace(go.Bar(x=names, y=means_b, name="変更前", marker_color=_NAVY))
    fig.add_trace(go.Bar(x=names, y=means_a, name="変更後", marker_color=_TEAL))
    fig.update_layout(
        barmode="group",
        title="変更前後 平均値比較",
        xaxis_title="変更名称", yaxis_title="平均値",
        height=360, plot_bgcolor=_BG, paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25),
    )
    return fig

"""仕入先品質複合スコアリング — Plotly チャート。"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

_NAVY  = "#1e3a5f"
_GREEN = "#16a34a"
_AMBER = "#d97706"
_RED   = "#dc2626"
_BG    = "#f5f7fa"

_VERDICT_COLOR = {"good": _GREEN, "warning": _AMBER, "alert": _RED}


def score_bar_chart(scored_df: pd.DataFrame) -> go.Figure:
    df = scored_df.sort_values("composite_score", ascending=True)
    colors = [_VERDICT_COLOR.get(v, _AMBER) for v in df["verdict"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["composite_score"],
        y=df["supplier_id"],
        orientation="h",
        marker_color=colors,
        name="合成スコア",
        text=df["composite_score"].round(1),
        textposition="outside",
    ))
    fig.add_vline(x=80, line_dash="dash", line_color=_NAVY,
                  annotation_text="80（good）", annotation_position="top")
    fig.add_vline(x=60, line_dash="dot", line_color=_AMBER,
                  annotation_text="60（warning）", annotation_position="bottom")
    fig.update_layout(
        title="仕入先別 合成スコア",
        xaxis=dict(title="合成スコア", range=[0, 110]),
        yaxis_title="仕入先",
        height=350,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        showlegend=False,
    )
    return fig


def breakdown_chart(scored_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=scored_df["supplier_id"], y=scored_df["defect_score"],
        name="不良スコア", marker_color=_RED,
    ))
    fig.add_trace(go.Bar(
        x=scored_df["supplier_id"], y=scored_df["delivery_score"],
        name="納期スコア", marker_color=_GREEN,
    ))
    fig.add_trace(go.Bar(
        x=scored_df["supplier_id"], y=scored_df["price_score"],
        name="価格スコア", marker_color=_NAVY,
    ))
    fig.update_layout(
        barmode="group",
        title="指標別スコア内訳",
        xaxis_title="仕入先",
        yaxis=dict(title="スコア（0〜100）", range=[0, 110]),
        height=350,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25),
    )
    return fig

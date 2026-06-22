"""仕入先品質複合スコアリング — Plotly チャート。"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

_BG    = "#f5f7fa"
_NAVY  = "#1e3a5f"
_GREEN = "#16a34a"
_RED   = "#dc2626"
_AMBER = "#d97706"
_TEAL  = "#0891b2"
_PURPLE = "#7c3aed"


def score_bar_chart(result_df: pd.DataFrame) -> go.Figure:
    """仕入先別 合計スコア + 内訳 積み上げ棒グラフ。"""
    suppliers = result_df["supplier"].tolist()
    ds = (result_df["defect_score"] * 0.4).tolist()
    cs = (result_df["cpk_score"]    * 0.4).tolist()
    ls = (result_df["claim_score"]  * 0.2).tolist()

    fig = go.Figure()
    fig.add_trace(go.Bar(x=suppliers, y=ds, name="受入不良率スコア(×0.4)", marker_color=_NAVY))
    fig.add_trace(go.Bar(x=suppliers, y=cs, name="Cpkスコア(×0.4)", marker_color=_TEAL))
    fig.add_trace(go.Bar(x=suppliers, y=ls, name="クレームスコア(×0.2)", marker_color=_AMBER))
    fig.add_hline(y=80.0, line_dash="dash", line_color=_GREEN,
                  annotation_text="80点（good）", annotation_position="right")
    fig.add_hline(y=60.0, line_dash="dash", line_color=_RED,
                  annotation_text="60点（alert）", annotation_position="right")
    fig.update_layout(
        barmode="stack", title="仕入先別 品質スコア（内訳）",
        xaxis_title="仕入先", yaxis=dict(title="スコア（点）", range=[0, 105]),
        height=380, plot_bgcolor=_BG, paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25),
    )
    return fig


def radar_chart(result_df: pd.DataFrame) -> go.Figure:
    """仕入先別 3指標スコア レーダーチャート。"""
    categories = ["受入不良率スコア", "Cpkスコア", "クレームスコア"]
    fig = go.Figure()
    palette = [_NAVY, _TEAL, _AMBER, _RED, _PURPLE]
    for i, row in result_df.iterrows():
        values = [row["defect_score"], row["cpk_score"], row["claim_score"]]
        values_closed = values + [values[0]]
        cats_closed   = categories + [categories[0]]
        fig.add_trace(go.Scatterpolar(
            r=values_closed, theta=cats_closed,
            fill="toself", name=row["supplier"],
            line=dict(color=palette[i % len(palette)]),
        ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title="仕入先別 品質スコア レーダーチャート",
        height=360, paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.1),
    )
    return fig

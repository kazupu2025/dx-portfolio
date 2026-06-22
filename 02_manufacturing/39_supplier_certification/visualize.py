"""サプライヤー品質認定 — Plotly チャート。"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

_BG = "#f5f7fa"
_NAVY = "#1e3a5f"
_GRN = "#16a34a"
_AMB = "#d97706"
_RED = "#dc2626"
_CERT_COLOR = {"認定": _GRN, "条件付認定": _AMB, "保留": _RED}


def score_bar_chart(df: pd.DataFrame) -> go.Figure:
    """サプライヤーの総合スコアを横棒グラフで表示。"""
    df_s = df.sort_values("total_score", ascending=True)
    colors = [_CERT_COLOR.get(c, _NAVY) for c in df_s["certification"].tolist()]
    fig = go.Figure(
        go.Bar(
            y=df_s["name"],
            x=df_s["total_score"],
            orientation="h",
            marker_color=colors,
            text=[
                f"{v:.1f}点 ({c})"
                for v, c in zip(df_s["total_score"], df_s["certification"])
            ],
            textposition="outside",
        )
    )
    fig.add_vline(
        x=80, line_dash="dash", line_color=_GRN, annotation_text="認定基準"
    )
    fig.add_vline(
        x=60, line_dash="dash", line_color=_RED, annotation_text="保留基準"
    )
    fig.update_layout(
        title="サプライヤー総合スコア（認定状況）",
        xaxis=dict(title="総合スコア", range=[0, 115]),
        height=max(300, len(df) * 50 + 100),
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
    )
    return fig


def radar_chart(row: pd.Series) -> go.Figure:
    """単一サプライヤーのレーダーチャート（品質・納期・コスト）。"""
    categories = ["品質(50%)", "納期(30%)", "コスト(20%)"]
    values = [
        float(row.get("quality_score", 0)),
        float(row.get("delivery_score", 0)),
        float(row.get("cost_score", 0)),
    ]
    values_closed = values + [values[0]]
    cats_closed = categories + [categories[0]]
    fig = go.Figure(
        go.Scatterpolar(
            r=values_closed,
            theta=cats_closed,
            fill="toself",
            fillcolor=f"{_NAVY}33",
            line=dict(color=_NAVY),
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title=f"{row.get('name', '')} スコア内訳",
        height=320,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
    )
    return fig

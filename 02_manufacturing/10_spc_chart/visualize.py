"""X-bar/R 管理図の Plotly 描画モジュール。"""
from __future__ import annotations
import plotly.graph_objects as go

_NAVY    = "#1e3a5f"
_ALERT   = "#dc2626"
_GREEN   = "#16a34a"
_BG      = "#f5f7fa"
_FONT    = "BIZ UDGothic"


def xbar_chart(result: dict, violations: dict[int, list[int]]) -> go.Figure:
    """
    X-bar 管理図を描画する。

    Parameters
    ----------
    result : dict
        analyze.run_analysis の返り値
    violations : dict[int, list[int]]
        rules.detect_violations の返り値（ルール番号→違反 index リスト）

    Returns
    -------
    go.Figure
    """
    subs   = result["subgroups"]
    labels = [s["label"] for s in subs]
    xbars  = [s["xbar"]  for s in subs]

    violated = set(idx for indices in violations.values() for idx in indices)
    colors   = [_ALERT if i in violated else _NAVY for i in range(len(xbars))]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=labels, y=xbars,
        mode="lines+markers",
        line=dict(color=_NAVY, width=1.5),
        marker=dict(color=colors, size=8, line=dict(width=1, color="white")),
        name="X̄",
    ))

    for y_val, lbl, color, dash in [
        (result["xbar_ucl"], f"UCL={result['xbar_ucl']:.4f}", _ALERT, "dash"),
        (result["xbar_cl"],  f"CL={result['xbar_cl']:.4f}",   _NAVY,  "dot"),
        (result["xbar_lcl"], f"LCL={result['xbar_lcl']:.4f}", _ALERT, "dash"),
    ]:
        fig.add_hline(
            y=y_val, line_dash=dash, line_color=color, line_width=1.2,
            annotation_text=lbl, annotation_position="right",
            annotation_font_size=10,
        )

    fig.update_layout(
        title=dict(text="X̄ 管理図", font=dict(size=14, color=_NAVY)),
        xaxis_title="サブグループ（ロット）",
        yaxis_title="平均値 X̄",
        font=dict(family=_FONT, size=12),
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        height=320,
        margin=dict(l=60, r=90, t=40, b=40),
        showlegend=False,
    )
    return fig


def r_chart(result: dict, violated_r_indices: list[int]) -> go.Figure:
    """
    R 管理図を描画する。

    Parameters
    ----------
    result : dict
        analyze.run_analysis の返り値
    violated_r_indices : list[int]
        rules.rule1_r の返り値（Rule 1 違反の index リスト）

    Returns
    -------
    go.Figure
    """
    subs   = result["subgroups"]
    labels = [s["label"] for s in subs]
    rs     = [s["r"]     for s in subs]
    colors = [_ALERT if i in violated_r_indices else _GREEN for i in range(len(rs))]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=labels, y=rs,
        mode="lines+markers",
        line=dict(color=_GREEN, width=1.5),
        marker=dict(color=colors, size=8, line=dict(width=1, color="white")),
        name="R",
    ))

    for y_val, lbl, color, dash in [
        (result["r_ucl"], f"UCL={result['r_ucl']:.4f}", _ALERT, "dash"),
        (result["r_cl"],  f"R̄={result['r_cl']:.4f}",   _GREEN, "dot"),
    ]:
        fig.add_hline(
            y=y_val, line_dash=dash, line_color=color, line_width=1.2,
            annotation_text=lbl, annotation_position="right",
            annotation_font_size=10,
        )

    if result["r_lcl"] > 0:
        fig.add_hline(
            y=result["r_lcl"], line_dash="dash", line_color=_ALERT, line_width=1.2,
            annotation_text=f"LCL={result['r_lcl']:.4f}",
            annotation_position="right", annotation_font_size=10,
        )

    fig.update_layout(
        title=dict(text="R 管理図", font=dict(size=14, color=_NAVY)),
        xaxis_title="サブグループ（ロット）",
        yaxis_title="範囲 R",
        font=dict(family=_FONT, size=12),
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        height=220,
        margin=dict(l=60, r=90, t=40, b=40),
        showlegend=False,
    )
    return fig

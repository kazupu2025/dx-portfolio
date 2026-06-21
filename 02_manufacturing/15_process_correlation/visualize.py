"""工程間品質相関分析 Plotly 描画モジュール。"""
from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go

_NAVY    = "#1e3a5f"
_ALERT   = "#dc2626"
_GREEN   = "#16a34a"
_WARNING = "#d97706"
_BG      = "#f5f7fa"
_FONT    = "BIZ UDGothic"


def heatmap_chart(corr_df: pd.DataFrame, pvalue_df: pd.DataFrame) -> go.Figure:
    """Pearson 相関行列のヒートマップ（-1=青〜0=白〜+1=赤）。
    p < 0.05 のセルには r 値に * を付与する。
    """
    cols = corr_df.columns.tolist()
    z = corr_df.values.tolist()

    text: list[list[str]] = []
    for i, row_col in enumerate(cols):
        row: list[str] = []
        for j, col in enumerate(cols):
            r_val = corr_df.iloc[i, j]
            p_val = pvalue_df.iloc[i, j]
            cell = f"{r_val:.2f}"
            if i != j and p_val < 0.05:
                cell += "*"
            row.append(cell)
        text.append(row)

    colorscale = [
        [0.0, _NAVY],
        [0.5, "#ffffff"],
        [1.0, _ALERT],
    ]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=cols,
        y=cols,
        text=text,
        texttemplate="%{text}",
        colorscale=colorscale,
        zmin=-1,
        zmax=1,
        colorbar=dict(title="r", thickness=12),
    ))
    fig.update_layout(
        title=dict(text="工程間 Pearson 相関行列", font=dict(size=14, color=_NAVY)),
        font=dict(family=_FONT, size=12),
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        height=400,
        margin=dict(l=60, r=60, t=50, b=60),
    )
    return fig


def scatter_chart(
    df: pd.DataFrame,
    col_x: str,
    col_y: str,
    r: float,
    pvalue: float,
) -> go.Figure:
    """最強相関ペアの散布図 + 回帰直線。"""
    x = pd.to_numeric(df[col_x], errors="coerce").dropna().to_numpy(dtype=float)
    y = pd.to_numeric(df[col_y], errors="coerce").dropna().to_numpy(dtype=float)

    min_len = min(len(x), len(y))
    x, y = x[:min_len], y[:min_len]

    m, b = np.polyfit(x, y, 1)
    x_line = np.array([x.min(), x.max()])
    y_line = m * x_line + b

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode="markers",
        name="データ",
        marker=dict(color=_WARNING, size=8, opacity=0.7),
        showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=x_line, y=y_line,
        mode="lines",
        name="回帰直線",
        line=dict(color=_NAVY, width=2),
        showlegend=False,
    ))
    fig.update_layout(
        title=dict(
            text=f"{col_x} vs {col_y}  r={r:.3f}  p={pvalue:.4f}",
            font=dict(size=13, color=_NAVY),
        ),
        xaxis_title=col_x,
        yaxis_title=col_y,
        font=dict(family=_FONT, size=12),
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        height=350,
        margin=dict(l=60, r=30, t=50, b=50),
    )
    return fig

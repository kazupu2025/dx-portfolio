"""ロットトレーサビリティ — Plotly グラフ可視化。"""
from __future__ import annotations
import networkx as nx
import plotly.graph_objects as go

_BG = "#f5f7fa"
_NAVY = "#1e3a5f"
_GREEN = "#16a34a"
_ORANGE = "#d97706"
_RED = "#dc2626"

_NODE_COLORS = {
    "material": "#16a34a",  # 原材料 = 緑
    "process": "#1e3a5f",  # 工程   = navy
    "destination": "#dc2626",  # 出荷先 = 赤
}

_EDGE_COLORS = {
    "材料→工程": "#16a34a",
    "工程→工程": "#1e3a5f",
    "工程→出荷": "#dc2626",
}


def traceability_graph(
    G: nx.DiGraph, material_nodes: list, destination_nodes: list
) -> go.Figure:
    """
    有向グラフの Plotly 可視化（階層レイアウト）。

    Args:
        G: networkx 有向グラフ
        material_nodes: 原材料ノードのリスト
        destination_nodes: 出荷先ノードのリスト

    Returns:
        Plotly Figure オブジェクト
    """
    pos = _hierarchical_layout(G, material_nodes, destination_nodes)

    # エッジトレース
    edge_traces = {}
    for u, v, data in G.edges(data=True):
        et = data.get("edge_type", "工程→工程")
        if et not in edge_traces:
            edge_traces[et] = {"x": [], "y": [], "color": _EDGE_COLORS.get(et, _NAVY)}
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_traces[et]["x"] += [x0, x1, None]
        edge_traces[et]["y"] += [y0, y1, None]

    fig = go.Figure()

    # エッジを描画
    for et, trace in edge_traces.items():
        fig.add_trace(
            go.Scatter(
                x=trace["x"],
                y=trace["y"],
                mode="lines",
                line=dict(color=trace["color"], width=2),
                name=et,
                hoverinfo="none",
            )
        )

    # ノードトレース
    node_x, node_y, node_text, node_colors = [], [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(str(node))
        if node in material_nodes:
            node_colors.append(_NODE_COLORS["material"])
        elif node in destination_nodes:
            node_colors.append(_NODE_COLORS["destination"])
        else:
            node_colors.append(_NODE_COLORS["process"])

    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            marker=dict(size=20, color=node_colors, line=dict(width=2, color="white")),
            text=node_text,
            textposition="top center",
            hoverinfo="text",
            name="ノード",
        )
    )

    fig.update_layout(
        title="ロットトレーサビリティ グラフ<br><sub>緑=原材料 / Navy=工程 / 赤=出荷先</sub>",
        showlegend=True,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=480,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
    )
    return fig


def _hierarchical_layout(
    G: nx.DiGraph, material_nodes: list, destination_nodes: list
) -> dict:
    """
    階層レイアウト: 原材料(左) → 工程(中) → 出荷先(右)。

    Args:
        G: networkx グラフ
        material_nodes: 原材料ノード
        destination_nodes: 出荷先ノード

    Returns:
        {node: (x, y)} の辞書
    """
    pos = {}
    process_nodes = [
        n
        for n in G.nodes()
        if n not in material_nodes and n not in destination_nodes
    ]

    def assign_column(nodes, x_val):
        """ノードを縦方向に配置。"""
        for i, n in enumerate(nodes):
            pos[n] = (x_val, -(i - len(nodes) / 2))

    assign_column(sorted(material_nodes), 0.0)
    assign_column(sorted(process_nodes), 1.5)
    assign_column(sorted(destination_nodes), 3.0)
    return pos


def lot_edge_table(df, lot_id: str) -> go.Figure:
    """
    特定ロットのエッジ一覧テーブル。

    Args:
        df: 元の DataFrame
        lot_id: フィルタ対象のロット ID

    Returns:
        Plotly Table Figure
    """
    filtered = df[df["lot_id"] == lot_id][["from_node", "to_node", "edge_type", "quantity"]]
    fig = go.Figure(
        go.Table(
            header=dict(
                values=["From", "To", "種別", "数量"],
                fill_color=_NAVY,
                font=dict(color="white"),
            ),
            cells=dict(values=[filtered[c].tolist() for c in filtered.columns]),
        )
    )
    fig.update_layout(title=f"ロット {lot_id} の追跡経路", height=200)
    return fig

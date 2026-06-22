"""ロットトレーサビリティ — networkx グラフ構築 + 分析。"""
from __future__ import annotations
import pandas as pd
import networkx as nx

REQUIRED_COLS = ["from_node", "to_node", "edge_type", "lot_id", "quantity"]


def _verdict(n_nodes: int) -> str:
    """ノード数に基づいて複雑度を判定。"""
    if n_nodes <= 10:
        return "good"
    elif n_nodes <= 20:
        return "warning"
    return "alert"


def run_analysis(df: pd.DataFrame) -> dict:
    """
    ロットトレーサビリティの分析を実行。

    Args:
        df: from_node, to_node, edge_type, lot_id, quantity 列を持つ DataFrame

    Returns:
        7キーの辞書:
        - G (nx.DiGraph): 有向グラフ
        - n_nodes (int): ノード数
        - n_edges (int): エッジ数
        - n_lots (int): ユニーク lot_id 数
        - material_nodes (list[str]): edge_type="材料→工程" の from_node
        - destination_nodes (list[str]): edge_type="工程→出荷" の to_node
        - verdict (str): "good" / "warning" / "alert"

    Raises:
        ValueError: 必須列が不足、または有効なデータがない場合
    """
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")

    data = df.copy().dropna(subset=["from_node", "to_node"])
    if len(data) == 0:
        raise ValueError("有効なデータがありません。")

    # グラフを構築
    G = nx.DiGraph()
    for _, row in data.iterrows():
        fn = str(row["from_node"])
        tn = str(row["to_node"])
        G.add_node(fn)
        G.add_node(tn)
        G.add_edge(
            fn,
            tn,
            edge_type=str(row["edge_type"]),
            lot_id=str(row["lot_id"]),
            quantity=float(row["quantity"]) if pd.notna(row.get("quantity")) else 0.0,
        )

    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    n_lots = int(data["lot_id"].nunique())

    material_nodes = sorted(
        set(data[data["edge_type"] == "材料→工程"]["from_node"].tolist())
    )
    destination_nodes = sorted(
        set(data[data["edge_type"] == "工程→出荷"]["to_node"].tolist())
    )

    return {
        "G": G,
        "n_nodes": n_nodes,
        "n_edges": n_edges,
        "n_lots": n_lots,
        "material_nodes": material_nodes,
        "destination_nodes": destination_nodes,
        "verdict": _verdict(n_nodes),
    }

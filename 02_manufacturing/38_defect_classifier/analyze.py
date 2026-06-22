"""不良原因自動分類 — 集計分析。"""
from __future__ import annotations
import pandas as pd
from classifier import classify_batch

REQUIRED_COLS = ["description"]


def run_analysis(df: pd.DataFrame) -> dict:
    """Analyze and classify defect descriptions.

    Args:
        df: DataFrame with 'description' column

    Returns:
        dict with result_df, category_counts, top_category, n_items, llm_used, verdict
    """
    if "description" not in df.columns:
        raise ValueError("必須列 'description' が不足しています。")
    data = df.copy()
    data = data.dropna(subset=["description"])
    data = data[data["description"].astype(str).str.strip() != ""].copy()
    if len(data) == 0:
        raise ValueError("有効なデータがありません。")

    texts = data["description"].astype(str).tolist()
    results, llm_used = classify_batch(texts)

    categories  = [r[0] for r in results]
    confidences = [r[1] for r in results]
    methods     = ["LLM" if llm_used else "ルールベース"] * len(results)

    result_df = data.copy().reset_index(drop=True)
    result_df["category"]   = categories
    result_df["confidence"] = confidences
    result_df["method"]     = methods

    category_counts = result_df["category"].value_counts().to_dict()
    top_category    = result_df["category"].mode()[0] if len(result_df) > 0 else "その他"
    verdict = "good" if llm_used else "warning"

    return {
        "result_df":       result_df,
        "category_counts": category_counts,
        "top_category":    top_category,
        "n_items":         len(result_df),
        "llm_used":        llm_used,
        "verdict":         verdict,
    }

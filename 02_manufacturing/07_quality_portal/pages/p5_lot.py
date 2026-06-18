"""⑤ ロット別合否判定一覧"""
import streamlit as st
from pages._pipeline_runner import SystemConfig, render_page


def _extract_kpis(r: dict) -> list:
    rate = r.get("pass_rate", 0)
    return [
        {
            "label": "合格率",
            "value": f"{rate:.2%}",
            "delta": None,
            "good": rate >= 0.95,
        },
        {
            "label": "不合格ロット数",
            "value": f"{r.get('failed_lots', 0)}件",
            "delta": None,
            "good": r.get("failed_lots", 0) == 0,
        },
        {
            "label": "要確認件数",
            "value": f"{r.get('review_count', 0)}件",
            "delta": None,
            "good": r.get("review_count", 0) == 0,
        },
    ]


cfg = SystemConfig(
    system_id="lot",
    title="⑤ ロット別合否判定一覧",
    description=(
        "ロット単位の合否を集計し、不合格ロットを特定します。\n"
        "製品別合格率・検査項目別不合格率・ロット一覧表を自動生成します。"
    ),
    required_columns=["ロットID", "製品名", "検査日", "検査項目", "判定"],
    sample_file="sample_lot.csv",
    pipeline_dir="lot",
    kpi_extractor=_extract_kpis,
)


def show():
    st.title(cfg.title)
    render_page(cfg)

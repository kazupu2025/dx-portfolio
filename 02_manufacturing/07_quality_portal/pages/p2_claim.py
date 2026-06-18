"""② クレーム件数集計レポート"""
import streamlit as st
from pages._pipeline_runner import SystemConfig, render_page


def _extract_kpis(r: dict) -> list:
    total = r.get("total_claims", 0)
    unresponded = r.get("unresponded", 0)
    return [
        {
            "label": "総クレーム数",
            "value": f"{total}件",
            "delta": None,
            "good": total < 10,
        },
        {
            "label": "未対応件数",
            "value": f"{unresponded}件",
            "delta": None,
            "good": unresponded == 0,
        },
        {
            "label": "最多クレーム仕入先",
            "value": r.get("top_supplier", "—"),
            "delta": None,
            "good": False,
        },
    ]


cfg = SystemConfig(
    system_id="claim",
    title="② クレーム件数集計レポート",
    description=(
        "仕入先からのクレームを集計し、対応状況を可視化します。\n"
        "未対応件数・カテゴリ別内訳・週次推移を自動レポートします。"
    ),
    required_columns=["日付", "仕入先名", "不良カテゴリ", "対応状況"],
    sample_file="sample_claim.csv",
    pipeline_dir="claim",
    kpi_extractor=_extract_kpis,
)


def show():
    st.title(cfg.title)
    render_page(cfg)

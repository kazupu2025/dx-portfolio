"""① 月次不良率集計レポート"""
import streamlit as st
from pages._pipeline_runner import SystemConfig, render_page


def _extract_kpis(r: dict) -> list:
    rate = r.get("total_defect_rate", 0)
    return [
        {
            "label": "総不良率",
            "value": f"{rate:.2%}",
            "delta": None,
            "good": rate < 0.05,
        },
        {
            "label": "最多不良ライン",
            "value": r.get("worst_line", "—"),
            "delta": None,
            "good": False,
        },
        {
            "label": "検査総数",
            "value": f"{r.get('total_inspected', 0):,}件",
            "delta": None,
            "good": True,
        },
    ]


cfg = SystemConfig(
    system_id="defect_rate",
    title="① 月次不良率集計レポート",
    description=(
        "製造ラインごとの不良率を集計し、問題ラインを特定します。\n"
        "月次CSVを読み込み、ライン別・製品別・日次の3種類のグラフを自動生成します。"
    ),
    required_columns=["日付", "ライン", "製品名", "検査数", "不良数"],
    sample_file="sample_defect_rate.csv",
    pipeline_dir="defect_rate",
    kpi_extractor=_extract_kpis,
)


def show():
    st.title(cfg.title)
    render_page(cfg)

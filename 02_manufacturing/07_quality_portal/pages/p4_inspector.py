"""④ 検査員別実績レポート"""
import streamlit as st
from pages._pipeline_runner import SystemConfig, render_page


def _extract_kpis(r: dict) -> list:
    rate = r.get("avg_pass_rate", 0)
    return [
        {
            "label": "総検査数",
            "value": f"{r.get('total_inspected', 0):,}件",
            "delta": None,
            "good": True,
        },
        {
            "label": "最高精度検査員",
            "value": r.get("best_inspector", "—"),
            "delta": None,
            "good": True,
        },
        {
            "label": "平均合格率",
            "value": f"{rate:.2%}",
            "delta": None,
            "good": rate >= 0.95,
        },
    ]


cfg = SystemConfig(
    system_id="inspector",
    title="④ 検査員別実績レポート",
    description=(
        "検査員ごとの合格率とシフト別実績を集計します。\n"
        "個人差・シフト差の可視化により、研修・配置改善に活用できます。"
    ),
    required_columns=["日付", "検査員名", "シフト", "検査数", "合格数"],
    sample_file="sample_inspector.csv",
    pipeline_dir="inspector",
    kpi_extractor=_extract_kpis,
)


def show():
    st.title(cfg.title)
    render_page(cfg)

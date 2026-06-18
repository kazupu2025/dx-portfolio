"""③ 歩留まりトレンドレポート"""
import streamlit as st
from pages._pipeline_runner import SystemConfig, render_page


def _extract_kpis(r: dict) -> list:
    rate = r.get("avg_yield_rate", 0)
    mom = r.get("mom_change")
    return [
        {
            "label": "平均歩留まり率",
            "value": f"{rate:.2%}",
            "delta": None,
            "good": rate >= 0.90,
        },
        {
            "label": "最低工程",
            "value": r.get("worst_process", "—"),
            "delta": None,
            "good": False,
        },
        {
            "label": "前月比",
            "value": "N/A" if mom is None else f"{mom:+.1f}%",
            "delta": None,
            "good": mom is None or mom >= 0,
        },
    ]


cfg = SystemConfig(
    system_id="yield_",
    title="③ 歩留まりトレンドレポート",
    description=(
        "工程別の歩留まり率を集計し、品質低下工程を特定します。\n"
        "週次トレンドと工程×週のヒートマップで変動を可視化します。"
    ),
    required_columns=["日付", "工程名", "投入数", "合格数"],
    sample_file="sample_yield.csv",
    pipeline_dir="yield_",
    kpi_extractor=_extract_kpis,
)


def show():
    st.title(cfg.title)
    render_page(cfg)

"""共通パイプライン実行・表示モジュール"""
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import pandas as pd
import streamlit as st

PORTAL_DIR = Path(__file__).parent.parent


@dataclass
class SystemConfig:
    system_id: str
    title: str
    description: str
    required_columns: list
    sample_file: str
    pipeline_dir: str
    kpi_extractor: Callable
    chart_files: list = field(default_factory=list)


def _kpi_card(label: str, value: str, delta: Optional[str], good: bool):
    color = "#16a34a" if good else "#dc2626"
    delta_html = f'<div style="font-size:0.8em;color:{color}">{delta}</div>' if delta else ""
    st.markdown(
        f"""<div style="background:#fff;border-radius:8px;padding:16px 20px;
            box-shadow:0 1px 4px rgba(0,0,0,.08);text-align:center">
            <div style="font-size:0.85em;color:#6b7280;margin-bottom:4px">{label}</div>
            <div style="font-size:1.8em;font-weight:700;color:#1e3a5f">{value}</div>
            {delta_html}
        </div>""",
        unsafe_allow_html=True,
    )


def render_page(cfg: SystemConfig):
    with st.expander("📋 このシステムについて", expanded=True):
        st.markdown(cfg.description)
        st.markdown("**必要な列：** " + " / ".join(f"`{c}`" for c in cfg.required_columns))

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        use_sample = st.button("▶ サンプルで今すぐ試す", use_container_width=True, type="primary")
    with col2:
        uploaded = st.file_uploader("📁 自分のCSVを使う", type=["csv"], label_visibility="collapsed")

    csv_path: Optional[Path] = None
    if use_sample:
        csv_path = PORTAL_DIR / cfg.sample_file
        st.info(f"サンプルデータ（{cfg.sample_file}）を使用します")
    elif uploaded:
        tmp_upload = Path(tempfile.mkdtemp()) / uploaded.name
        tmp_upload.write_bytes(uploaded.read())
        csv_path = tmp_upload
        st.success(f"アップロード完了: {uploaded.name}")

    if csv_path is None:
        return

    st.divider()
    progress = st.progress(0, text="準備中...")

    src = PORTAL_DIR / "pipelines" / cfg.pipeline_dir
    tmp = Path(tempfile.mkdtemp())
    error_msg = ""
    success = False

    try:
        shutil.copy(csv_path, tmp)
        (tmp / "output").mkdir()
        (tmp / "output" / "charts").mkdir()
        for script in ["cleanse.py", "analyze.py", "visualize.py"]:
            shutil.copy(src / script, tmp)

        step_labels = ["クレンジング中...", "分析中...", "グラフ生成中..."]
        step_pcts = [33, 66, 100]

        for i, script in enumerate(["cleanse.py", "analyze.py", "visualize.py"]):
            progress.progress(step_pcts[i] - 10, text=step_labels[i])
            r = subprocess.run(
                [sys.executable, script],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if r.returncode != 0:
                error_msg = f"**{script}** でエラーが発生しました:\n\n```\n{r.stderr[-800:]}\n```"
                break
            progress.progress(step_pcts[i], text=f"{script} 完了")
        else:
            success = True
    except Exception as e:
        error_msg = str(e)

    progress.empty()

    if not success:
        st.error("⚠️ パイプラインでエラーが発生しました")
        st.markdown(error_msg)
        with st.expander("よくある原因"):
            st.markdown(
                "- CSVの文字コードが UTF-8 でない\n"
                "- 必要な列名が異なる（半角スペース・漢字の違いなど）\n"
                f"- 必要な列: {', '.join(cfg.required_columns)}\n"
                "- 数値列に文字が混入している"
            )
        shutil.rmtree(tmp, ignore_errors=True)
        return

    result_json = {}
    result_path = tmp / "output" / "result_analysis.json"
    if result_path.exists():
        result_json = json.loads(result_path.read_text(encoding="utf-8"))

    st.subheader("📊 分析結果")
    kpis = cfg.kpi_extractor(result_json)
    cols = st.columns(len(kpis))
    for col, kpi in zip(cols, kpis):
        with col:
            _kpi_card(kpi["label"], kpi["value"], kpi.get("delta"), kpi.get("good", True))

    st.markdown("<br>", unsafe_allow_html=True)

    tab_report, tab_charts, tab_check, tab_dl = st.tabs(
        ["📄 レポート", "📈 グラフ", "✅ 品質チェック", "⬇ ダウンロード"]
    )

    with tab_report:
        report_path = tmp / "output" / "analysis_report.md"
        if report_path.exists():
            st.markdown(report_path.read_text(encoding="utf-8"))
        else:
            st.warning("レポートが見つかりません")

    with tab_charts:
        charts_dir = tmp / "output" / "charts"
        chart_files = sorted(charts_dir.glob("*.png"))
        if chart_files:
            for chart_file in chart_files:
                st.image(str(chart_file), use_container_width=True)
        else:
            st.warning("グラフが見つかりません")

    with tab_check:
        results = result_json.get("results", [])
        if results:
            for item in results:
                icon = "✅" if item.get("status") == "PASS" else "❌"
                st.markdown(f"{icon} {item.get('name', '')}")
            passed = result_json.get("passed", 0)
            total = len(results)
            if passed == total:
                st.success(f"全 {total} 項目チェック完了")
            else:
                st.warning(f"{total - passed} 件の問題が検出されました")
        else:
            st.info("品質チェック結果なし")

    with tab_dl:
        report_path = tmp / "output" / "analysis_report.md"
        candidates = list((tmp / "output").glob("cleaned_*.csv"))
        cleaned_path = candidates[0] if candidates else None

        if cleaned_path and cleaned_path.exists():
            st.download_button(
                "📥 クレンジング済みCSV をダウンロード",
                data=cleaned_path.read_bytes(),
                file_name=cleaned_path.name,
                mime="text/csv",
                use_container_width=True,
            )
        if report_path.exists():
            st.download_button(
                "📄 分析レポート（MD）をダウンロード",
                data=report_path.read_text(encoding="utf-8").encode("utf-8"),
                file_name="analysis_report.md",
                mime="text/markdown",
                use_container_width=True,
            )

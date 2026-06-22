# CAPA 完了率・期限遵守率レポート Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 月次 CAPA 実績 CSV を集計し、完了率・期限遵守率を算出して月次トレンドを可視化する月次レポートツールを実装する。

**Architecture:** CSV（month/total/completed/on_time_completed）→ analyze.py（完了率 + verdict）→ visualize.py（折れ線トレンド + 件数積み上げ棒）→ app.py（Streamlit UI + DB）の一方向依存。verdict は「高いほど good」（従来と逆向き）。

**Tech Stack:** Python 3.x, Streamlit, Plotly, pandas

---

### Task 1: scaffold + sample_data.py

**Files:**
- Create: `02_manufacturing/22_capa_report/sample_data.py`
- Create: `02_manufacturing/22_capa_report/tests/__init__.py`
- Create: `02_manufacturing/22_capa_report/STATUS.md`

- [ ] **Step 1: ディレクトリ作成**

```bash
mkdir -p "02_manufacturing/22_capa_report/tests"
```

- [ ] **Step 2: `tests/__init__.py` を作成（空ファイル）**

- [ ] **Step 3: `sample_data.py` を作成**

```python
"""6ヶ月（2024-01〜2024-06）CAPA 実績デモデータ生成。"""
from __future__ import annotations
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    """6ヶ月 = 6行のサンプルデータを生成する。

    列: month, total, completed, on_time_completed
    期待値: completion_rate ≈ 82% → verdict = "warning"
            ontime_rate ≈ 72%
    """
    data = {
        "month":             ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"],
        "total":             [12,        15,        10,        13,        14,        11],
        "completed":         [10,        13,        8,         10,        12,        9],
        "on_time_completed": [9,         11,        8,         8,         10,        8],
    }
    # total=75 / completed=62 → completion_rate=82.7% → warning
    # on_time_completed=54 → ontime_rate=72.0%
    return pd.DataFrame(data)


if __name__ == "__main__":
    df = generate_sample_csv()
    total = df["total"].sum()
    comp  = df["completed"].sum()
    ontime = df["on_time_completed"].sum()
    print(f"total={total}, completion_rate={comp/total*100:.1f}%, ontime_rate={ontime/total*100:.1f}%")
    df.to_csv("sample_capa_report.csv", index=False)
```

- [ ] **Step 4: `STATUS.md` を作成**

```markdown
# C-76 CAPA完了率・期限遵守率レポート

- name: CAPA完了率・期限遵守率レポート
- industry: 製造
- department: 品質保証
- status: in-progress
```

- [ ] **Step 5: syntax チェック + 実データ確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -c "import ast; ast.parse(open('02_manufacturing/22_capa_report/sample_data.py', encoding='utf-8').read()); print('OK')"
cd "02_manufacturing/22_capa_report"
python sample_data.py
```

期待: `completion_rate ≈ 82.7% → warning`

- [ ] **Step 6: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/22_capa_report/
git commit -m "feat(C-76): scaffold + sample_data.py（6ヶ月 CAPA 実績デモ）"
```

---

### Task 2: TDD — test_analyze.py + analyze.py

**Files:**
- Create: `02_manufacturing/22_capa_report/tests/test_analyze.py`
- Create: `02_manufacturing/22_capa_report/analyze.py`

- [ ] **Step 1: `test_analyze.py` を作成（RED フェーズ）**

```python
"""C-76 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze  # noqa: E402


def _make_df(months, totals, completed, on_time):
    return pd.DataFrame({
        "month":             months,
        "total":             totals,
        "completed":         completed,
        "on_time_completed": on_time,
    })


def test_verdict_good():
    # completed=9/total=10 → rate=90.0% → good（境界値）
    df = _make_df(["2024-01"], [10], [9], [8])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["completion_rate"] == pytest.approx(90.0)


def test_verdict_warning():
    # completed=8/total=10 → rate=80.0% → warning
    df = _make_df(["2024-01"], [10], [8], [7])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 70.0 <= result["completion_rate"] < 90.0


def test_verdict_alert():
    # completed=6/total=10 → rate=60.0% → alert
    df = _make_df(["2024-01"], [10], [6], [5])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["completion_rate"] < 70.0


def test_verdict_warning_lower_boundary():
    # completed=7/total=10 → rate=70.0% → warning（下限境界値、alertではない）
    df = _make_df(["2024-01"], [10], [7], [6])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert result["completion_rate"] == pytest.approx(70.0)


def test_total_capas():
    # 2ヶ月合計: 10 + 15 = 25
    df = _make_df(["2024-01", "2024-02"], [10, 15], [8, 12], [7, 10])
    result = analyze.run_analysis(df)
    assert result["total_capas"] == 25


def test_completion_rate():
    # completed=18 / total=25 = 72.0%
    df = _make_df(["2024-01", "2024-02"], [10, 15], [8, 10], [7, 8])
    result = analyze.run_analysis(df)
    assert result["completion_rate"] == pytest.approx(72.0)


def test_open_count():
    # total=25 - completed=18 = 7
    df = _make_df(["2024-01", "2024-02"], [10, 15], [8, 10], [7, 8])
    result = analyze.run_analysis(df)
    assert result["open_count"] == 7


def test_missing_column_raises():
    df = pd.DataFrame({"month": ["2024-01"], "total": [10]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)
```

- [ ] **Step 2: テストが FAIL することを確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\02_manufacturing\22_capa_report"
python -m pytest tests/test_analyze.py -v 2>&1 | head -10
```

- [ ] **Step 3: `analyze.py` を作成（GREEN フェーズ）**

```python
"""CAPA 完了率・期限遵守率レポート — 完了率集計 + verdict ロジック。"""
from __future__ import annotations

import pandas as pd

REQUIRED_COLS = ["month", "total", "completed", "on_time_completed"]


def _verdict(rate: float) -> str:
    if rate >= 90.0:
        return "good"
    elif rate >= 70.0:
        return "warning"
    return "alert"


def run_analysis(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")

    data = df.copy()
    for col in ["total", "completed", "on_time_completed"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=["total", "completed", "on_time_completed"])
    data = data[data["total"] > 0].copy()

    if len(data) < 1:
        raise ValueError("有効なデータがありません。")

    total_capas = int(data["total"].sum())
    n_months = int(data["month"].nunique())
    avg_monthly_capas = float(total_capas / n_months)

    total_completed = data["completed"].sum()
    total_ontime = data["on_time_completed"].sum()

    completion_rate = float(total_completed / total_capas * 100)
    ontime_rate = float(total_ontime / total_capas * 100)
    open_count = int(total_capas - total_completed)

    return {
        "result_df":         data,
        "total_capas":       total_capas,
        "avg_monthly_capas": avg_monthly_capas,
        "completion_rate":   completion_rate,
        "ontime_rate":       ontime_rate,
        "open_count":        open_count,
        "verdict":           _verdict(completion_rate),
    }
```

- [ ] **Step 4: 全テストが PASS することを確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\02_manufacturing\22_capa_report"
python -m pytest tests/test_analyze.py -v
```

期待: `8 passed`

- [ ] **Step 5: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/22_capa_report/analyze.py \
        02_manufacturing/22_capa_report/tests/test_analyze.py
git commit -m "feat(C-76): analyze.py TDD — 8テスト all PASS（CAPA完了率 + 期限遵守率 verdict）"
```

---

### Task 3: visualize.py

**Files:**
- Create: `02_manufacturing/22_capa_report/visualize.py`

- [ ] **Step 1: `visualize.py` を作成**

```python
"""CAPA 完了率・期限遵守率レポート — Plotly チャート。"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

_BG     = "#f5f7fa"
_BLUE   = "#1e3a5f"
_TEAL   = "#0891b2"
_GREEN  = "#16a34a"
_RED    = "#dc2626"
_AMBER  = "#d97706"


def rate_trend_chart(result_df: pd.DataFrame) -> go.Figure:
    """完了率 + 期限遵守率 月次折れ線グラフ。

    result_df must contain columns: month, total, completed, on_time_completed.
    """
    months = sorted(result_df["month"].unique())
    monthly = (
        result_df.groupby("month")[["total", "completed", "on_time_completed"]]
        .sum()
        .reindex(months)
    )
    comp_rates   = (monthly["completed"]         / monthly["total"] * 100).tolist()
    ontime_rates = (monthly["on_time_completed"]  / monthly["total"] * 100).tolist()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months, y=comp_rates, mode="lines+markers",
        name="完了率", line=dict(color=_BLUE, width=2),
        marker=dict(size=8),
    ))
    fig.add_trace(go.Scatter(
        x=months, y=ontime_rates, mode="lines+markers",
        name="期限遵守率", line=dict(color=_TEAL, width=2, dash="dot"),
        marker=dict(size=8),
    ))
    fig.add_hline(y=90.0, line_dash="dash", line_color=_GREEN,
                  annotation_text="90%（good）", annotation_position="right")
    fig.add_hline(y=70.0, line_dash="dash", line_color=_RED,
                  annotation_text="70%（alert）", annotation_position="right")
    fig.update_layout(
        title="CAPA 完了率・期限遵守率 月次推移",
        xaxis_title="年月",
        yaxis=dict(title="率（%）", range=[0, 105]),
        height=380,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25),
    )
    return fig


def monthly_bar_chart(result_df: pd.DataFrame) -> go.Figure:
    """月次 CAPA 件数 積み上げ棒グラフ（完了 / 未完了）。

    result_df must contain columns: month, total, completed.
    """
    months = sorted(result_df["month"].unique())
    monthly = (
        result_df.groupby("month")[["total", "completed"]]
        .sum()
        .reindex(months)
    )
    completed = monthly["completed"].tolist()
    open_cnt  = (monthly["total"] - monthly["completed"]).tolist()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=months, y=completed, name="完了",
        marker_color=_GREEN,
    ))
    fig.add_trace(go.Bar(
        x=months, y=open_cnt, name="未完了",
        marker_color=_RED,
    ))
    fig.update_layout(
        barmode="stack",
        title="月次 CAPA 件数（完了 / 未完了）",
        xaxis_title="年月",
        yaxis_title="件数（件）",
        height=320,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25),
    )
    return fig
```

- [ ] **Step 2: syntax + import チェック**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -c "import ast; ast.parse(open('02_manufacturing/22_capa_report/visualize.py', encoding='utf-8').read()); print('syntax OK')"
cd "02_manufacturing/22_capa_report"
python -c "import visualize; print('import OK')"
```

- [ ] **Step 3: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/22_capa_report/visualize.py
git commit -m "feat(C-76): visualize.py — 完了率折れ線 + CAPA件数積み上げ棒"
```

---

### Task 4: app.py + STATUS.md

**Files:**
- Create: `02_manufacturing/22_capa_report/app.py`
- Modify: `02_manufacturing/22_capa_report/STATUS.md`

- [ ] **Step 1: `app.py` を作成**

```python
"""CAPA 完了率・期限遵守率レポート — CAPA 管理状況モニタリング。"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import analyze
import visualize
from sample_data import generate_sample_csv

st.set_page_config(page_title="CAPA完了率・期限遵守率レポート", page_icon="✅", layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #f5f7fa; }
[data-testid="stHeader"] { background-color: #f5f7fa; }
.block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div style="background:#1e3a5f;color:white;padding:12px 20px;'
    'border-radius:6px;margin-bottom:16px">'
    '<h3 style="margin:0;font-family:BIZ UDGothic">'
    "✅ CAPA 完了率・期限遵守率レポート</h3>"
    "</div>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙ 設定")
    st.caption("CSV 列: month / total / completed / on_time_completed")
    uploaded   = st.file_uploader("CSVアップロード", type=["csv"])
    use_sample = st.button("サンプルデータを使用", use_container_width=True)

    if uploaded:
        st.session_state["df"] = pd.read_csv(uploaded)
    elif use_sample:
        st.session_state["df"] = generate_sample_csv()

    df: pd.DataFrame | None = st.session_state.get("df")
    run_btn = False
    if df is not None:
        run_btn = st.button("▶ 分析実行", type="primary", use_container_width=True)

if df is None:
    st.info("サイドバーから CSV をアップロードするか、「サンプルデータを使用」をクリックしてください。")
    st.stop()

if run_btn:
    try:
        result = analyze.run_analysis(df)
        st.session_state.update({
            "result":        result,
            "uploaded_name": uploaded.name if uploaded else "sample_capa_report.csv",
            "row_count":     len(df),
        })
    except ValueError as e:
        st.error(str(e))
        st.stop()

    try:
        from _common.db_writer import init_db, write_upload, write_kpi
        init_db()
        uid = write_upload(
            "capa_report",
            st.session_state.get("uploaded_name"),
            st.session_state.get("row_count"),
        )
        write_kpi(
            uid, "capa_report",
            datetime.now().strftime("%Y-%m"),
            "completion_rate",
            float(st.session_state["result"]["completion_rate"]),
            st.session_state["result"]["verdict"],
        )
    except Exception as _e:
        st.caption(f"⚠ DB書き込みスキップ: {_e}")

result = st.session_state.get("result")
if not result:
    st.info("「▶ 分析実行」を押してください。")
    st.stop()

avg_capas  = result["avg_monthly_capas"]
comp_rate  = result["completion_rate"]
ontime     = result["ontime_rate"]
verdict    = result["verdict"]

_COLOR = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_LABEL = {"good": "CAPA管理良好", "warning": "要注意", "alert": "要改善"}
v_color = _COLOR[verdict]
v_label = _LABEL[verdict]

c1, c2, c3, c4 = st.columns(4)
c1.metric("月次平均 CAPA 件数", f"{avg_capas:.1f}件")
c2.metric("完了率", f"{comp_rate:.1f}%")
c3.metric("期限遵守率", f"{ontime:.1f}%")
c4.markdown(
    f'<div style="background:{v_color}22;border-left:4px solid {v_color};'
    f'padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{v_color};font-size:16px">{v_label}</b><br>'
    f'<span style="font-size:12px;color:#64748b">完了率={comp_rate:.1f}%</span>'
    f'</div>',
    unsafe_allow_html=True,
)

col_l, col_r = st.columns([2, 1])
with col_l:
    st.plotly_chart(
        visualize.rate_trend_chart(result["result_df"]),
        use_container_width=True,
    )
with col_r:
    st.plotly_chart(
        visualize.monthly_bar_chart(result["result_df"]),
        use_container_width=True,
    )

st.subheader("CAPA 実績詳細")
display_df = (
    result["result_df"][["month", "total", "completed", "on_time_completed"]]
    .sort_values("month")
    .reset_index(drop=True)
)
display_df["完了率(%)"] = (display_df["completed"] / display_df["total"] * 100).round(1)
display_df["遵守率(%)"] = (display_df["on_time_completed"] / display_df["total"] * 100).round(1)
st.dataframe(display_df, use_container_width=True)
```

- [ ] **Step 2: `STATUS.md` を production-ready に更新**

```markdown
# C-76 CAPA完了率・期限遵守率レポート

- name: CAPA完了率・期限遵守率レポート
- industry: 製造
- department: 品質保証
- status: production-ready
```

- [ ] **Step 3: syntax + テスト確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -c "import ast; ast.parse(open('02_manufacturing/22_capa_report/app.py', encoding='utf-8').read()); print('OK')"
cd "02_manufacturing/22_capa_report" && python -m pytest tests/test_analyze.py -v
```

- [ ] **Step 4: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/22_capa_report/app.py 02_manufacturing/22_capa_report/STATUS.md
git commit -m "feat(C-76): app.py + STATUS.md production-ready（CAPA完了率 + 期限遵守率 + DB）"
```

---

### Task 5: dashboard.py + catalog.yml 更新

**Files:**
- Modify: `02_manufacturing/09_unified_dashboard/dashboard.py`
- Modify: `catalog.yml`

- [ ] **Step 1: `dashboard.py` CARDS 末尾（`quality_cost` の直後）に追加**

```python
    {"system_id": "capa_report", "metric": "completion_rate",
     "title": "CAPA完了率", "fmt": lambda v: f"{v:.1f}%"},
```

- [ ] **Step 2: `catalog.yml` 末尾に C-76 エントリを追記**

```yaml
- id: "C-76"
  name: "CAPA完了率・期限遵守率レポート"
  industry: "製造"
  department: "品質保証"
  difficulty: "★★★"
  status: "production-ready"
  priority: "A"
  path: "02_manufacturing/22_capa_report"
  demo: "streamlit run 02_manufacturing/22_capa_report/app.py"
  description: |
    月次の CAPA 実績（登録・完了・期限内完了）を CSV でアップロードし、
    完了率と期限遵守率を自動算出。完了率 ≥ 90% → "good" の高いほど良い verdict 設計。
    折れ線トレンドと月次件数積み上げ棒グラフで改善ポイントを可視化。
```

- [ ] **Step 3: 全テスト確認**

```bash
python -m pytest 02_manufacturing/22_capa_report/tests/ -v
```

- [ ] **Step 4: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/09_unified_dashboard/dashboard.py catalog.yml
git commit -m "feat(C-76): C-63ダッシュボード + catalog.yml に C-76 追加"
```

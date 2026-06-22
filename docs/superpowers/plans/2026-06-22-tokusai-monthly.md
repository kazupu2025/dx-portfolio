# 特採件数・理由別集計・月次推移 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 月次特採件数（理由別）CSV を集計し、月次推移と理由別内訳を可視化するレポートツールを実装する。

**Architecture:** CSV（month/reason/count）→ analyze.py（月次集計 + verdict）→ visualize.py（積み上げ棒グラフ + 理由別横棒）→ app.py（Streamlit UI + DB）。C-74 クレームとほぼ同一パターン。

**Tech Stack:** Python 3.x, Streamlit, Plotly, pandas

---

### Task 1: scaffold + sample_data.py

**Files:**
- Create: `02_manufacturing/23_tokusai_monthly/sample_data.py`
- Create: `02_manufacturing/23_tokusai_monthly/tests/__init__.py`
- Create: `02_manufacturing/23_tokusai_monthly/STATUS.md`

- [ ] **Step 1: ディレクトリ作成**

```bash
mkdir -p "02_manufacturing/23_tokusai_monthly/tests"
```

- [ ] **Step 2: `tests/__init__.py` を作成（空ファイル）**

- [ ] **Step 3: `sample_data.py` を作成**

```python
"""5理由 × 6ヶ月 特採件数デモデータ生成。"""
from __future__ import annotations
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    """5理由 × 6ヶ月 = 30行のサンプルデータを生成する。

    列: month, reason, count
    期待値: avg_monthly ≈ 7件 → verdict = "warning"
            top_reason: 寸法軽微逸脱
    """
    months = ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]

    data = {
        "寸法軽微逸脱":   [3, 4, 3, 4, 3, 4],
        "外観不良":       [2, 2, 1, 2, 2, 1],
        "機能上問題なし": [1, 1, 1, 1, 1, 1],
        "材料代替":       [1, 0, 1, 0, 1, 0],
        "その他":         [0, 1, 0, 1, 0, 1],
    }

    rows = []
    for reason, counts in data.items():
        for i, month in enumerate(months):
            rows.append({"month": month, "reason": reason, "count": counts[i]})

    # 月合計: ≈ 7件 → avg_monthly=7.0 → warning
    # top_reason: 寸法軽微逸脱（合計 ≈ 21件）
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_sample_csv()
    total = df["count"].sum()
    avg = total / df["month"].nunique()
    top = df.groupby("reason")["count"].sum().idxmax()
    print(f"total={total}, avg_monthly={avg:.1f}, top_reason={top}")
    df.to_csv("sample_tokusai.csv", index=False)
```

- [ ] **Step 4: `STATUS.md` を作成**

```markdown
# C-77 特採件数・理由別集計・月次推移

- name: 特採件数・理由別集計・月次推移
- industry: 製造
- department: 品質保証
- status: in-progress
```

- [ ] **Step 5: syntax チェック + 実データ確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -c "import ast; ast.parse(open('02_manufacturing/23_tokusai_monthly/sample_data.py', encoding='utf-8').read()); print('OK')"
cd "02_manufacturing/23_tokusai_monthly" && python sample_data.py
```

- [ ] **Step 6: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/23_tokusai_monthly/
git commit -m "feat(C-77): scaffold + sample_data.py（5理由 × 6ヶ月 特採デモ）"
```

---

### Task 2: TDD — test_analyze.py + analyze.py

**Files:**
- Create: `02_manufacturing/23_tokusai_monthly/tests/test_analyze.py`
- Create: `02_manufacturing/23_tokusai_monthly/analyze.py`

- [ ] **Step 1: `test_analyze.py` を作成（RED フェーズ）**

```python
"""C-77 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze  # noqa: E402


def _make_df(months, reasons, counts):
    return pd.DataFrame({"month": months, "reason": reasons, "count": counts})


def test_verdict_good():
    # 1ヶ月 total=3 → avg=3.0 → good（境界値）
    df = _make_df(["2024-01"], ["寸法軽微逸脱"], [3])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["avg_monthly_count"] == pytest.approx(3.0)


def test_verdict_warning():
    # 1ヶ月 total=7 → avg=7.0 → warning
    df = _make_df(["2024-01"], ["寸法軽微逸脱"], [7])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 3.0 < result["avg_monthly_count"] <= 10.0


def test_verdict_alert():
    # 1ヶ月 total=15 → avg=15.0 → alert
    df = _make_df(["2024-01"], ["寸法軽微逸脱"], [15])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["avg_monthly_count"] > 10.0


def test_verdict_warning_upper_boundary():
    # 1ヶ月 total=10 → avg=10.0 → warning（上限境界値）
    df = _make_df(["2024-01"], ["寸法軽微逸脱"], [10])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert result["avg_monthly_count"] == pytest.approx(10.0)


def test_total_count():
    # 3行合計 = 2+3+5 = 10
    df = _make_df(
        ["2024-01", "2024-01", "2024-01"],
        ["寸法軽微逸脱", "外観不良", "その他"],
        [2, 3, 5],
    )
    result = analyze.run_analysis(df)
    assert result["total_count"] == 10


def test_top_reason():
    # 寸法軽微逸脱: 8件 > 外観不良: 3件
    df = _make_df(
        ["2024-01", "2024-01", "2024-01"],
        ["寸法軽微逸脱", "外観不良", "寸法軽微逸脱"],
        [5, 3, 3],
    )
    result = analyze.run_analysis(df)
    assert result["top_reason"] == "寸法軽微逸脱"


def test_n_reasons():
    # 3種類の理由
    df = _make_df(
        ["2024-01", "2024-01", "2024-01"],
        ["寸法軽微逸脱", "外観不良", "その他"],
        [2, 3, 1],
    )
    result = analyze.run_analysis(df)
    assert result["n_reasons"] == 3


def test_missing_column_raises():
    df = pd.DataFrame({"month": ["2024-01"], "reason": ["寸法軽微逸脱"]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)
```

- [ ] **Step 2: テストが FAIL することを確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\02_manufacturing\23_tokusai_monthly"
python -m pytest tests/test_analyze.py -v 2>&1 | head -10
```

- [ ] **Step 3: `analyze.py` を作成（GREEN フェーズ）**

```python
"""特採件数・理由別集計・月次推移 — 集計 + verdict ロジック。"""
from __future__ import annotations

import pandas as pd

REQUIRED_COLS = ["month", "reason", "count"]


def _verdict(avg: float) -> str:
    if avg <= 3.0:
        return "good"
    elif avg <= 10.0:
        return "warning"
    return "alert"


def run_analysis(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")

    data = df.copy()
    data["count"] = pd.to_numeric(data["count"], errors="coerce")
    data = data.dropna(subset=["count"])
    data = data[data["count"] >= 0].copy()

    if len(data) < 1:
        raise ValueError("有効なデータがありません。")

    total_count = int(data["count"].sum())
    n_months = int(data["month"].nunique())
    avg_monthly_count = float(total_count / n_months)

    reason_totals = data.groupby("reason")["count"].sum()
    top_reason = str(reason_totals.idxmax())
    n_reasons = int(data["reason"].nunique())

    return {
        "result_df":         data,
        "total_count":       total_count,
        "avg_monthly_count": avg_monthly_count,
        "top_reason":        top_reason,
        "n_reasons":         n_reasons,
        "verdict":           _verdict(avg_monthly_count),
    }
```

- [ ] **Step 4: 全テスト PASS 確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\02_manufacturing\23_tokusai_monthly"
python -m pytest tests/test_analyze.py -v
```

期待: `8 passed`

- [ ] **Step 5: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/23_tokusai_monthly/analyze.py \
        02_manufacturing/23_tokusai_monthly/tests/test_analyze.py
git commit -m "feat(C-77): analyze.py TDD — 8テスト all PASS（特採集計 + verdict）"
```

---

### Task 3: visualize.py

**Files:**
- Create: `02_manufacturing/23_tokusai_monthly/visualize.py`

- [ ] **Step 1: `visualize.py` を作成**

```python
"""特採件数・理由別集計・月次推移 — Plotly チャート。"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

_NAVY   = "#1e3a5f"
_GREEN  = "#16a34a"
_RED    = "#dc2626"
_BG     = "#f5f7fa"

_PALETTE = [
    "#1e3a5f", "#16a34a", "#d97706", "#dc2626",
    "#7c3aed", "#0891b2", "#be185d", "#65a30d",
]


def trend_chart(result_df: pd.DataFrame) -> go.Figure:
    """理由別 月次件数 積み上げ棒グラフ。

    result_df must contain columns: month, reason, count.
    """
    months  = sorted(result_df["month"].unique())
    reasons = sorted(result_df["reason"].unique())

    pivot = (
        result_df.groupby(["month", "reason"])["count"]
        .sum()
        .reset_index()
        .pivot(index="month", columns="reason", values="count")
        .reindex(months)
        .fillna(0)
    )

    fig = go.Figure()
    for i, reason in enumerate(reasons):
        if reason not in pivot.columns:
            continue
        fig.add_trace(go.Bar(
            x=months,
            y=pivot[reason].tolist(),
            name=reason,
            marker_color=_PALETTE[i % len(_PALETTE)],
        ))

    fig.add_hline(y=10.0, line_dash="dash", line_color=_RED,
                  annotation_text="10件（alert）", annotation_position="right")
    fig.add_hline(y=3.0, line_dash="dash", line_color=_GREEN,
                  annotation_text="3件（good）", annotation_position="right")
    fig.update_layout(
        barmode="stack",
        title="特採件数 月次推移（理由別）",
        xaxis_title="年月",
        yaxis_title="特採件数（件）",
        height=380,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25),
    )
    return fig


def reason_bar_chart(result_df: pd.DataFrame) -> go.Figure:
    """理由別 総特採件数 横棒グラフ（降順）。

    result_df must contain columns: reason, count.
    """
    reason_totals = (
        result_df.groupby("reason")["count"]
        .sum()
        .sort_values(ascending=True)
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=reason_totals.values,
        y=reason_totals.index,
        orientation="h",
        marker_color=_NAVY,
        text=[f"{int(v)}件" for v in reason_totals.values],
        textposition="outside",
    ))
    fig.update_layout(
        title="理由別 特採件数",
        xaxis=dict(title="件数（件）", range=[0, None]),
        yaxis_title="理由",
        height=320,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        showlegend=False,
    )
    return fig
```

- [ ] **Step 2: syntax + import チェック**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -c "import ast; ast.parse(open('02_manufacturing/23_tokusai_monthly/visualize.py', encoding='utf-8').read()); print('syntax OK')"
cd "02_manufacturing/23_tokusai_monthly" && python -c "import visualize; print('import OK')"
```

- [ ] **Step 3: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/23_tokusai_monthly/visualize.py
git commit -m "feat(C-77): visualize.py — 理由別積み上げ棒グラフ + 横棒グラフ"
```

---

### Task 4: app.py + STATUS.md

**Files:**
- Create: `02_manufacturing/23_tokusai_monthly/app.py`
- Modify: `02_manufacturing/23_tokusai_monthly/STATUS.md`

- [ ] **Step 1: `app.py` を作成**

```python
"""特採件数・理由別集計・月次推移 — 特採管理モニタリング。"""
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

st.set_page_config(page_title="特採件数・理由別集計", page_icon="📋", layout="wide")

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
    "📋 特採件数・理由別集計・月次推移</h3>"
    "</div>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙ 設定")
    st.caption("CSV 列: month / reason / count")
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
            "uploaded_name": uploaded.name if uploaded else "sample_tokusai.csv",
            "row_count":     len(df),
        })
    except ValueError as e:
        st.error(str(e))
        st.stop()

    try:
        from _common.db_writer import init_db, write_upload, write_kpi
        init_db()
        uid = write_upload(
            "tokusai_monthly",
            st.session_state.get("uploaded_name"),
            st.session_state.get("row_count"),
        )
        write_kpi(
            uid, "tokusai_monthly",
            datetime.now().strftime("%Y-%m"),
            "count",
            float(st.session_state["result"]["avg_monthly_count"]),
            st.session_state["result"]["verdict"],
        )
    except Exception as _e:
        st.caption(f"⚠ DB書き込みスキップ: {_e}")

result = st.session_state.get("result")
if not result:
    st.info("「▶ 分析実行」を押してください。")
    st.stop()

avg    = result["avg_monthly_count"]
top_r  = result["top_reason"]
n_r    = result["n_reasons"]
verdict = result["verdict"]

_COLOR = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_LABEL = {"good": "特採少", "warning": "要注意", "alert": "要改善"}
v_color = _COLOR[verdict]
v_label = _LABEL[verdict]

c1, c2, c3, c4 = st.columns(4)
c1.metric("月次平均件数", f"{avg:.1f}件")
c2.metric("最多理由", top_r)
c3.metric("理由分類数", f"{n_r}種")
c4.markdown(
    f'<div style="background:{v_color}22;border-left:4px solid {v_color};'
    f'padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{v_color};font-size:16px">{v_label}</b><br>'
    f'<span style="font-size:12px;color:#64748b">avg={avg:.1f}件/月</span>'
    f'</div>',
    unsafe_allow_html=True,
)

col_l, col_r = st.columns([2, 1])
with col_l:
    st.plotly_chart(
        visualize.trend_chart(result["result_df"]),
        use_container_width=True,
    )
with col_r:
    st.plotly_chart(
        visualize.reason_bar_chart(result["result_df"]),
        use_container_width=True,
    )

st.subheader("特採データ詳細")
display_df = (
    result["result_df"][["month", "reason", "count"]]
    .sort_values(["month", "reason"])
    .reset_index(drop=True)
)
st.dataframe(display_df, use_container_width=True)
```

- [ ] **Step 2: `STATUS.md` を production-ready に更新**

```markdown
# C-77 特採件数・理由別集計・月次推移

- name: 特採件数・理由別集計・月次推移
- industry: 製造
- department: 品質保証
- status: production-ready
```

- [ ] **Step 3: syntax + テスト確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -c "import ast; ast.parse(open('02_manufacturing/23_tokusai_monthly/app.py', encoding='utf-8').read()); print('OK')"
cd "02_manufacturing/23_tokusai_monthly" && python -m pytest tests/test_analyze.py -v
```

- [ ] **Step 4: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/23_tokusai_monthly/app.py 02_manufacturing/23_tokusai_monthly/STATUS.md
git commit -m "feat(C-77): app.py + STATUS.md production-ready（特採集計 + 理由別 + DB）"
```

---

### Task 5: dashboard.py + catalog.yml

**Files:**
- Modify: `02_manufacturing/09_unified_dashboard/dashboard.py`
- Modify: `catalog.yml`

- [ ] **Step 1: `dashboard.py` CARDS 末尾（`capa_report` の直後）に追加**

```python
    {"system_id": "tokusai_monthly", "metric": "count",
     "title": "特採月次平均", "fmt": lambda v: f"{v:.1f}件"},
```

- [ ] **Step 2: `catalog.yml` 末尾に C-77 エントリを追記**

```yaml
- id: "C-77"
  name: "特採件数・理由別集計・月次推移"
  industry: "製造"
  department: "品質保証"
  difficulty: "★★★"
  status: "production-ready"
  priority: "A"
  path: "02_manufacturing/23_tokusai_monthly"
  demo: "streamlit run 02_manufacturing/23_tokusai_monthly/app.py"
  description: |
    月次の特採件数を理由別に集計し、月次推移と理由別内訳を自動集計。
    月次平均 ≤ 3件 → "good" の明快な verdict 設計。
    積み上げ棒グラフと理由別横棒グラフで改善ポイントを可視化。
```

- [ ] **Step 3: テスト確認**

```bash
python -m pytest 02_manufacturing/23_tokusai_monthly/tests/ -v
```

- [ ] **Step 4: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/09_unified_dashboard/dashboard.py catalog.yml
git commit -m "feat(C-77): C-63ダッシュボード + catalog.yml に C-77 追加"
```

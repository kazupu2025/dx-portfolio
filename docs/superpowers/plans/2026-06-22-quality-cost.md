# 品質コスト明細集計（4分類）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 月次品質コスト明細（予防・評価・内部損失・外部損失）CSV を集計し、損失コスト比率と月次トレンドを可視化する月次レポートツールを実装する。

**Architecture:** CSV（month/category/amount）→ analyze.py（コスト集計 + failure_ratio + verdict）→ visualize.py（積み上げ棒グラフ + 分類別横棒）→ app.py（Streamlit UI + DB）の一方向依存。C-74 と同一パターン。

**Tech Stack:** Python 3.x, Streamlit, Plotly, pandas

---

## ファイルマップ

| ファイル | 役割 |
|---------|------|
| `02_manufacturing/21_quality_cost/sample_data.py` | 6ヶ月 × 4分類 デモデータ生成 |
| `02_manufacturing/21_quality_cost/analyze.py` | コスト集計 + failure_ratio + verdict（純粋関数）|
| `02_manufacturing/21_quality_cost/visualize.py` | Plotly 積み上げ棒グラフ + 分類別横棒 |
| `02_manufacturing/21_quality_cost/app.py` | Streamlit UI + DB 書き込み |
| `02_manufacturing/21_quality_cost/STATUS.md` | production-ready |
| `02_manufacturing/21_quality_cost/tests/__init__.py` | 空（パッケージマーカー）|
| `02_manufacturing/21_quality_cost/tests/test_analyze.py` | 8テスト TDD |
| `02_manufacturing/09_unified_dashboard/dashboard.py` | CARDS に quality_cost 追加（修正）|
| `catalog.yml` | C-75 エントリ追加（修正）|

---

### Task 1: scaffold + sample_data.py

**Files:**
- Create: `02_manufacturing/21_quality_cost/sample_data.py`
- Create: `02_manufacturing/21_quality_cost/tests/__init__.py`
- Create: `02_manufacturing/21_quality_cost/STATUS.md`

- [ ] **Step 1: ディレクトリ作成**

```bash
mkdir -p "02_manufacturing/21_quality_cost/tests"
```

- [ ] **Step 2: `tests/__init__.py` を作成（空ファイル）**

- [ ] **Step 3: `sample_data.py` を作成**

```python
"""6ヶ月（2024-01〜2024-06）× 4分類 品質コスト デモデータ生成。"""
from __future__ import annotations
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    """6ヶ月 × 4分類 = 24行のサンプルデータを生成する。

    列: month, category, amount
    期待値: failure_ratio ≈ 46% → verdict = "warning"
            dominant_category: 評価コスト
    """
    months = ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]

    # 分類別月次金額（円）
    data = {
        "予防コスト":   [150000, 155000, 148000, 152000, 160000, 145000],
        "評価コスト":   [200000, 210000, 195000, 205000, 215000, 200000],
        "内部損失コスト": [180000, 175000, 185000, 170000, 190000, 178000],
        "外部損失コスト": [120000, 130000, 115000, 125000, 135000, 118000],
    }

    rows = []
    for cat, amounts in data.items():
        for i, month in enumerate(months):
            rows.append({
                "month":    month,
                "category": cat,
                "amount":   amounts[i],
            })

    # 期待値:
    # 予防 ≈ 910,000 / 評価 ≈ 1,225,000 / 内部損失 ≈ 1,078,000 / 外部損失 ≈ 743,000
    # total ≈ 3,956,000 / failure_ratio ≈ (1,078,000+743,000)/3,956,000 ≈ 46.1% → warning
    # dominant_category: 評価コスト
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_sample_csv()
    total = df["amount"].sum()
    n_months = df["month"].nunique()
    avg = total / n_months
    failure = df[df["category"].isin(["内部損失コスト", "外部損失コスト"])]["amount"].sum()
    ratio = failure / total * 100
    print(f"total={total:,}, avg_monthly={avg:,.0f}, failure_ratio={ratio:.1f}%")
    df.to_csv("sample_quality_cost.csv", index=False)
```

- [ ] **Step 4: `STATUS.md` を作成**

```markdown
# C-75 品質コスト明細集計（4分類）

- name: 品質コスト明細集計（4分類）
- industry: 製造
- department: 品質保証
- status: in-progress
```

- [ ] **Step 5: syntax チェック**

```bash
python -c "import ast; ast.parse(open('02_manufacturing/21_quality_cost/sample_data.py', encoding='utf-8').read()); print('OK')"
```

- [ ] **Step 6: 実データ確認**

```bash
cd "02_manufacturing/21_quality_cost"
python sample_data.py
```

failure_ratio が 40〜55% 範囲内であることを確認する。

- [ ] **Step 7: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/21_quality_cost/
git commit -m "feat(C-75): scaffold + sample_data.py（6ヶ月 × 4分類 品質コストデモ）"
```

---

### Task 2: TDD — test_analyze.py + analyze.py

**Files:**
- Create: `02_manufacturing/21_quality_cost/tests/test_analyze.py`
- Create: `02_manufacturing/21_quality_cost/analyze.py`

- [ ] **Step 1: `test_analyze.py` を作成（RED フェーズ）**

```python
"""C-75 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze  # noqa: E402


def _make_df(months, categories, amounts):
    return pd.DataFrame({
        "month":    months,
        "category": categories,
        "amount":   amounts,
    })


def test_verdict_good():
    # 内部損失20 + 外部損失10 = 30 / total=100 → ratio=30.0% → good（境界値）
    df = _make_df(
        ["2024-01", "2024-01", "2024-01", "2024-01"],
        ["予防コスト", "評価コスト", "内部損失コスト", "外部損失コスト"],
        [40, 30, 20, 10],
    )
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["failure_ratio"] == pytest.approx(30.0)


def test_verdict_warning():
    # ratio = 40% → warning
    df = _make_df(
        ["2024-01", "2024-01", "2024-01", "2024-01"],
        ["予防コスト", "評価コスト", "内部損失コスト", "外部損失コスト"],
        [30, 30, 25, 15],
    )
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 30.0 < result["failure_ratio"] <= 50.0


def test_verdict_alert():
    # ratio = 60% → alert
    df = _make_df(
        ["2024-01", "2024-01", "2024-01", "2024-01"],
        ["予防コスト", "評価コスト", "内部損失コスト", "外部損失コスト"],
        [20, 20, 40, 20],
    )
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["failure_ratio"] > 50.0


def test_verdict_warning_upper_boundary():
    # 内部損失30 + 外部損失20 = 50 / total=100 → ratio=50.0% → warning（上限境界値）
    df = _make_df(
        ["2024-01", "2024-01", "2024-01", "2024-01"],
        ["予防コスト", "評価コスト", "内部損失コスト", "外部損失コスト"],
        [30, 20, 30, 20],
    )
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert result["failure_ratio"] == pytest.approx(50.0)


def test_total_cost():
    # 100 + 200 + 300 + 400 = 1000
    df = _make_df(
        ["2024-01"] * 4,
        ["予防コスト", "評価コスト", "内部損失コスト", "外部損失コスト"],
        [100, 200, 300, 400],
    )
    result = analyze.run_analysis(df)
    assert result["total_cost"] == 1000


def test_cost_by_category():
    # 2ヶ月分: 評価コスト = 200 + 300 = 500
    df = _make_df(
        ["2024-01", "2024-01", "2024-02", "2024-02"],
        ["評価コスト", "予防コスト", "評価コスト", "予防コスト"],
        [200, 100, 300, 150],
    )
    result = analyze.run_analysis(df)
    assert result["cost_by_category"]["評価コスト"] == 500
    assert result["cost_by_category"]["予防コスト"] == 250


def test_dominant_category():
    # 評価コスト: 500 > 予防コスト: 250 → dominant = 評価コスト
    df = _make_df(
        ["2024-01", "2024-01", "2024-01", "2024-01"],
        ["予防コスト", "評価コスト", "内部損失コスト", "外部損失コスト"],
        [100, 500, 200, 200],
    )
    result = analyze.run_analysis(df)
    assert result["dominant_category"] == "評価コスト"


def test_missing_column_raises():
    df = pd.DataFrame({"month": ["2024-01"], "category": ["予防コスト"]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)
```

- [ ] **Step 2: テストが FAIL することを確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\02_manufacturing\21_quality_cost"
python -m pytest tests/test_analyze.py -v 2>&1 | head -10
```

期待: `ModuleNotFoundError` または `ImportError`

- [ ] **Step 3: `analyze.py` を作成（GREEN フェーズ）**

```python
"""品質コスト明細集計（4分類）— コスト集計 + 損失コスト比率 + verdict ロジック。"""
from __future__ import annotations

import pandas as pd

REQUIRED_COLS = ["month", "category", "amount"]
FAILURE_CATEGORIES = ["内部損失コスト", "外部損失コスト"]


def _verdict(ratio: float) -> str:
    if ratio <= 30.0:
        return "good"
    elif ratio <= 50.0:
        return "warning"
    return "alert"


def run_analysis(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")

    data = df.copy()
    data["amount"] = pd.to_numeric(data["amount"], errors="coerce")
    data = data.dropna(subset=["amount"])
    data = data[data["amount"] >= 0].copy()

    if len(data) < 1:
        raise ValueError("有効なデータがありません。")

    total_cost = int(data["amount"].sum())
    n_months = int(data["month"].nunique())
    avg_monthly_cost = float(total_cost / n_months)

    cat_totals = data.groupby("category")["amount"].sum()
    cost_by_category = {str(k): int(v) for k, v in cat_totals.items()}
    dominant_category = str(cat_totals.idxmax())

    failure_amount = sum(cost_by_category.get(cat, 0) for cat in FAILURE_CATEGORIES)
    failure_ratio = float(failure_amount / total_cost * 100) if total_cost > 0 else 0.0

    return {
        "result_df":         data,
        "total_cost":        total_cost,
        "avg_monthly_cost":  avg_monthly_cost,
        "cost_by_category":  cost_by_category,
        "dominant_category": dominant_category,
        "failure_ratio":     failure_ratio,
        "verdict":           _verdict(failure_ratio),
    }
```

- [ ] **Step 4: 全テストが PASS することを確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\02_manufacturing\21_quality_cost"
python -m pytest tests/test_analyze.py -v
```

期待: `8 passed`

- [ ] **Step 5: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/21_quality_cost/analyze.py \
        02_manufacturing/21_quality_cost/tests/test_analyze.py
git commit -m "feat(C-75): analyze.py TDD — 8テスト all PASS（品質コスト集計 + 損失比率 verdict）"
```

---

### Task 3: visualize.py

**Files:**
- Create: `02_manufacturing/21_quality_cost/visualize.py`

- [ ] **Step 1: `visualize.py` を作成**

```python
"""品質コスト明細集計（4分類）— Plotly チャート。"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

_BG = "#f5f7fa"

# PAF モデルの 4 分類カラー
_CAT_COLOR = {
    "予防コスト":    "#16a34a",   # green
    "評価コスト":    "#0891b2",   # info blue
    "内部損失コスト": "#d97706",  # amber
    "外部損失コスト": "#dc2626",  # red
}
_DEFAULT_COLOR = "#1e3a5f"

_CATEGORY_ORDER = ["予防コスト", "評価コスト", "内部損失コスト", "外部損失コスト"]


def monthly_cost_chart(result_df: pd.DataFrame) -> go.Figure:
    """月次 × 4分類 の積み上げ棒グラフ。

    result_df must contain columns: month, category, amount.
    """
    months = sorted(result_df["month"].unique())

    pivot = (
        result_df.groupby(["month", "category"])["amount"]
        .sum()
        .reset_index()
        .pivot(index="month", columns="category", values="amount")
        .reindex(months)
        .fillna(0)
    )

    fig = go.Figure()
    for cat in _CATEGORY_ORDER:
        if cat not in pivot.columns:
            continue
        fig.add_trace(go.Bar(
            x=months,
            y=pivot[cat].tolist(),
            name=cat,
            marker_color=_CAT_COLOR.get(cat, _DEFAULT_COLOR),
        ))

    fig.update_layout(
        barmode="stack",
        title="品質コスト月次推移（4分類）",
        xaxis_title="年月",
        yaxis_title="コスト（円）",
        height=380,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25),
        yaxis=dict(tickformat=","),
    )
    return fig


def category_bar_chart(result_df: pd.DataFrame) -> go.Figure:
    """分類別 総コスト 横棒グラフ（金額降順）。

    result_df must contain columns: category, amount.
    """
    cat_totals = (
        result_df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=True)  # 横棒は ascending=True で多い順が上
    )

    colors = [_CAT_COLOR.get(str(cat), _DEFAULT_COLOR) for cat in cat_totals.index]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=cat_totals.values,
        y=cat_totals.index,
        orientation="h",
        marker_color=colors,
        text=[f"¥{int(v):,}" for v in cat_totals.values],
        textposition="outside",
    ))
    fig.update_layout(
        title="分類別 品質コスト合計",
        xaxis=dict(title="コスト（円）", tickformat=",", range=[0, None]),
        yaxis_title="分類",
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
python -c "import ast; ast.parse(open('02_manufacturing/21_quality_cost/visualize.py', encoding='utf-8').read()); print('syntax OK')"
```

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\02_manufacturing\21_quality_cost"
python -c "import visualize; print('import OK')"
```

- [ ] **Step 3: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/21_quality_cost/visualize.py
git commit -m "feat(C-75): visualize.py — 積み上げ棒グラフ + 分類別横棒（PAF 4分類カラー）"
```

---

### Task 4: app.py + STATUS.md（production-ready）

**Files:**
- Create: `02_manufacturing/21_quality_cost/app.py`
- Modify: `02_manufacturing/21_quality_cost/STATUS.md`

- [ ] **Step 1: `app.py` を作成**

```python
"""品質コスト明細集計（4分類）— 損失コスト比率 × 月次トレンド可視化。"""
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

st.set_page_config(page_title="品質コスト明細集計（4分類）", page_icon="💴", layout="wide")

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
    "💴 品質コスト明細集計（4分類）</h3>"
    "</div>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙ 設定")
    st.caption("CSV 列: month / category / amount")
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
            "uploaded_name": uploaded.name if uploaded else "sample_quality_cost.csv",
            "row_count":     len(df),
        })
    except ValueError as e:
        st.error(str(e))
        st.stop()

    try:
        from _common.db_writer import init_db, write_upload, write_kpi
        init_db()
        uid = write_upload(
            "quality_cost",
            st.session_state.get("uploaded_name"),
            st.session_state.get("row_count"),
        )
        write_kpi(
            uid, "quality_cost",
            datetime.now().strftime("%Y-%m"),
            "failure_ratio",
            float(st.session_state["result"]["failure_ratio"]),
            st.session_state["result"]["verdict"],
        )
    except Exception as _e:
        st.caption(f"⚠ DB書き込みスキップ: {_e}")

result = st.session_state.get("result")
if not result:
    st.info("「▶ 分析実行」を押してください。")
    st.stop()

avg_cost   = result["avg_monthly_cost"]
dom_cat    = result["dominant_category"]
ratio      = result["failure_ratio"]
verdict    = result["verdict"]

_COLOR = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_LABEL = {"good": "品質管理良好", "warning": "要注意", "alert": "要改善"}
v_color = _COLOR[verdict]
v_label = _LABEL[verdict]

c1, c2, c3, c4 = st.columns(4)
c1.metric("月次平均コスト", f"¥{avg_cost:,.0f}")
c2.metric("最大コスト分類", dom_cat)
c3.metric("損失コスト比率", f"{ratio:.1f}%")
c4.markdown(
    f'<div style="background:{v_color}22;border-left:4px solid {v_color};'
    f'padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{v_color};font-size:16px">{v_label}</b><br>'
    f'<span style="font-size:12px;color:#64748b">損失比率={ratio:.1f}%</span>'
    f'</div>',
    unsafe_allow_html=True,
)

col_l, col_r = st.columns([2, 1])
with col_l:
    st.plotly_chart(
        visualize.monthly_cost_chart(result["result_df"]),
        use_container_width=True,
    )
with col_r:
    st.plotly_chart(
        visualize.category_bar_chart(result["result_df"]),
        use_container_width=True,
    )

st.subheader("品質コスト詳細")
display_df = (
    result["result_df"][["month", "category", "amount"]]
    .sort_values(["month", "category"])
    .reset_index(drop=True)
)
display_df["amount"] = display_df["amount"].apply(lambda v: f"¥{int(v):,}")
st.dataframe(display_df, use_container_width=True)
```

- [ ] **Step 2: `STATUS.md` を production-ready に更新**

```markdown
# C-75 品質コスト明細集計（4分類）

- name: 品質コスト明細集計（4分類）
- industry: 製造
- department: 品質保証
- status: production-ready
```

- [ ] **Step 3: syntax チェック**

```bash
python -c "import ast; ast.parse(open('02_manufacturing/21_quality_cost/app.py', encoding='utf-8').read()); print('OK')"
```

- [ ] **Step 4: 全テスト確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\02_manufacturing\21_quality_cost"
python -m pytest tests/test_analyze.py -v
```

期待: `8 passed`

- [ ] **Step 5: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/21_quality_cost/app.py \
        02_manufacturing/21_quality_cost/STATUS.md
git commit -m "feat(C-75): app.py + STATUS.md production-ready（品質コスト × 損失比率 + DB）"
```

---

### Task 5: dashboard.py + catalog.yml 更新

**Files:**
- Modify: `02_manufacturing/09_unified_dashboard/dashboard.py`（CARDS に追加）
- Modify: `catalog.yml`（C-75 エントリ追加）

- [ ] **Step 1: `dashboard.py` の CARDS リスト末尾（`customer_claim_monthly` の直後）に追加**

```python
    {"system_id": "quality_cost", "metric": "failure_ratio",
     "title": "損失コスト比率", "fmt": lambda v: f"{v:.1f}%"},
```

- [ ] **Step 2: `catalog.yml` の末尾に C-75 エントリを追記**

```yaml
- id: "C-75"
  name: "品質コスト明細集計（4分類）"
  industry: "製造"
  department: "品質保証"
  difficulty: "★★★"
  status: "production-ready"
  priority: "A"
  path: "02_manufacturing/21_quality_cost"
  demo: "streamlit run 02_manufacturing/21_quality_cost/app.py"
  description: |
    月次の品質コスト明細（予防・評価・内部損失・外部損失）を CSV でアップロードし、
    損失コスト比率を自動算出。損失比率 ≤ 30% → "good" の明快な verdict 設計。
    積み上げ棒グラフと分類別横棒グラフで改善ポイントを可視化。
```

- [ ] **Step 3: 全テスト確認**

```bash
python -m pytest 02_manufacturing/21_quality_cost/tests/ -v
```

期待: `8 passed`

- [ ] **Step 4: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/09_unified_dashboard/dashboard.py catalog.yml
git commit -m "feat(C-75): C-63ダッシュボード + catalog.yml に C-75 追加"
```

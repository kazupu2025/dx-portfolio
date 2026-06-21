# 顧客クレーム件数・原因分類 月次集計 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 顧客別・原因分類別クレーム件数 CSV を月次集計し、月次トレンドと原因分類内訳を可視化する月次レポートツールを実装する。

**Architecture:** CSV（customer/month/category/count）→ analyze.py（月次集計 + verdict）→ visualize.py（月次トレンド棒グラフ + 原因分類横棒）→ app.py（Streamlit UI + DB）の一方向依存。C-73 と同一パターン、ロジックは除算→加算でよりシンプル。

**Tech Stack:** Python 3.x, Streamlit, Plotly, pandas

---

## ファイルマップ

| ファイル | 役割 |
|---------|------|
| `02_manufacturing/20_customer_claim_monthly/sample_data.py` | 5顧客 × 6ヶ月 × 3分類 デモデータ生成 |
| `02_manufacturing/20_customer_claim_monthly/analyze.py` | クレーム集計 + verdict（純粋関数）|
| `02_manufacturing/20_customer_claim_monthly/visualize.py` | Plotly 月次トレンド + 原因分類横棒 |
| `02_manufacturing/20_customer_claim_monthly/app.py` | Streamlit UI + DB 書き込み |
| `02_manufacturing/20_customer_claim_monthly/STATUS.md` | production-ready |
| `02_manufacturing/20_customer_claim_monthly/tests/__init__.py` | 空（パッケージマーカー）|
| `02_manufacturing/20_customer_claim_monthly/tests/test_analyze.py` | 8テスト TDD |
| `02_manufacturing/09_unified_dashboard/dashboard.py` | CARDS に customer_claim_monthly 追加（修正）|
| `catalog.yml` | C-74 エントリ追加（修正）|

---

### Task 1: scaffold + sample_data.py

**Files:**
- Create: `02_manufacturing/20_customer_claim_monthly/sample_data.py`
- Create: `02_manufacturing/20_customer_claim_monthly/tests/__init__.py`
- Create: `02_manufacturing/20_customer_claim_monthly/STATUS.md`

- [ ] **Step 1: ディレクトリ作成**

```bash
mkdir -p "02_manufacturing/20_customer_claim_monthly/tests"
```

- [ ] **Step 2: `tests/__init__.py` を作成（空ファイル）**

- [ ] **Step 3: `sample_data.py` を作成**

```python
"""5顧客（A社〜E社）× 6ヶ月（2024-01〜2024-06）× 3原因分類 デモデータ生成。"""
from __future__ import annotations
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    """5顧客（A社〜E社）× 6ヶ月 × 3原因分類 = 90行のサンプルデータを生成する。

    列: customer, month, category, count
    期待値: avg_monthly ≈ 12件 → verdict = "warning"
            top_category: 寸法不良 / worst_customer: C社
    """
    rows = []
    months = ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]
    categories = ["寸法不良", "外観不良", "機能不良"]

    # A社: 少ない（good水準、計 ≈ 18件/6ヶ月）
    data_a = {
        "寸法不良": [2, 1, 2, 1, 2, 1],
        "外観不良": [1, 1, 0, 1, 0, 1],
        "機能不良": [0, 1, 0, 0, 1, 0],
    }
    # B社: 中程度（計 ≈ 36件/6ヶ月）
    data_b = {
        "寸法不良": [3, 4, 3, 4, 3, 3],
        "外観不良": [2, 1, 2, 1, 2, 2],
        "機能不良": [1, 1, 1, 1, 0, 1],
    }
    # C社: 最多（worst_customer、計 ≈ 60件/6ヶ月）
    data_c = {
        "寸法不良": [6, 7, 6, 7, 6, 6],
        "外観不良": [3, 2, 3, 2, 3, 3],
        "機能不良": [2, 2, 1, 2, 1, 2],
    }
    # D社: 少ない（計 ≈ 12件/6ヶ月）
    data_d = {
        "寸法不良": [1, 1, 1, 1, 1, 1],
        "外観不良": [0, 1, 0, 1, 0, 0],
        "機能不良": [0, 0, 1, 0, 0, 0],
    }
    # E社: 中程度（計 ≈ 30件/6ヶ月）
    data_e = {
        "寸法不良": [2, 3, 2, 3, 2, 3],
        "外観不良": [2, 1, 2, 1, 2, 1],
        "機能不良": [1, 0, 1, 0, 1, 0],
    }

    for customer, data in [
        ("A社", data_a), ("B社", data_b), ("C社", data_c),
        ("D社", data_d), ("E社", data_e),
    ]:
        for cat in categories:
            for i, month in enumerate(months):
                rows.append({
                    "customer": customer,
                    "month":    month,
                    "category": cat,
                    "count":    data[cat][i],
                })

    # 期待値: total ≈ 156件 / 6ヶ月 = avg 26件/月 → verdict = "alert"
    # top_category: 寸法不良 / worst_customer: C社
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_sample_csv()
    df.to_csv("sample_customer_claim.csv", index=False)
    print(df.to_string())
```

**注意:** avg_monthly は月ごとの全顧客合計の平均。上記データでは 1ヶ月あたりの合計がどの月も ≈ 26件のため verdict = "alert" になる。"warning" にしたい場合は件数を減らすこと。

- [ ] **Step 4: `STATUS.md` を作成**

```markdown
# C-74 顧客クレーム件数・原因分類 月次集計

- name: 顧客クレーム件数・原因分類 月次集計
- industry: 製造
- department: 品質保証
- status: in-progress
```

- [ ] **Step 5: syntax チェック**

```bash
python -c "import ast; ast.parse(open('02_manufacturing/20_customer_claim_monthly/sample_data.py', encoding='utf-8').read()); print('OK')"
```

期待出力: `OK`

- [ ] **Step 6: 実データで avg 確認**

```bash
cd "02_manufacturing/20_customer_claim_monthly"
python sample_data.py
```

avg_monthly を確認する（仕様 ≈ 12件想定だが実データ次第）。

- [ ] **Step 7: コミット**

```bash
git add 02_manufacturing/20_customer_claim_monthly/
git commit -m "feat(C-74): scaffold + sample_data.py（5顧客 × 6ヶ月 × 3分類 クレームデモ）"
```

---

### Task 2: TDD — test_analyze.py + analyze.py

**Files:**
- Create: `02_manufacturing/20_customer_claim_monthly/tests/test_analyze.py`
- Create: `02_manufacturing/20_customer_claim_monthly/analyze.py`

- [ ] **Step 1: `test_analyze.py` を作成（RED フェーズ）**

```python
"""C-74 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze  # noqa: E402


def _make_df(customers, months, categories, counts):
    return pd.DataFrame({
        "customer": customers,
        "month":    months,
        "category": categories,
        "count":    counts,
    })


def test_verdict_good():
    # 1ヶ月 total=5 → avg=5.0 → good（境界値）
    df = _make_df(["A社"], ["2024-01"], ["寸法不良"], [5])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["avg_monthly_claims"] == pytest.approx(5.0)


def test_verdict_warning():
    # 1ヶ月 total=10 → avg=10.0 → warning
    df = _make_df(["A社"], ["2024-01"], ["寸法不良"], [10])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 5.0 < result["avg_monthly_claims"] <= 15.0


def test_verdict_alert():
    # 1ヶ月 total=20 → avg=20.0 → alert
    df = _make_df(["A社"], ["2024-01"], ["寸法不良"], [20])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["avg_monthly_claims"] > 15.0


def test_verdict_warning_upper_boundary():
    # 1ヶ月 total=15 → avg=15.0 → warning（上限境界値、alertではない）
    df = _make_df(["A社"], ["2024-01"], ["寸法不良"], [15])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert result["avg_monthly_claims"] == pytest.approx(15.0)


def test_total_claims():
    # 3行 count合計 = 2+3+5 = 10
    df = _make_df(
        ["A社", "B社", "A社"],
        ["2024-01", "2024-01", "2024-01"],
        ["寸法不良", "寸法不良", "外観不良"],
        [2, 3, 5],
    )
    result = analyze.run_analysis(df)
    assert result["total_claims"] == 10


def test_top_category():
    # 寸法不良: 8件, 外観不良: 3件 → top = 寸法不良
    df = _make_df(
        ["A社", "A社", "B社"],
        ["2024-01", "2024-01", "2024-01"],
        ["寸法不良", "外観不良", "寸法不良"],
        [5, 3, 3],
    )
    result = analyze.run_analysis(df)
    assert result["top_category"] == "寸法不良"


def test_worst_customer():
    # A社: 8件, B社: 3件, C社: 1件 → worst = A社
    df = _make_df(
        ["A社", "A社", "B社", "C社"],
        ["2024-01", "2024-01", "2024-01", "2024-01"],
        ["寸法不良", "外観不良", "寸法不良", "寸法不良"],
        [5, 3, 3, 1],
    )
    result = analyze.run_analysis(df)
    assert result["worst_customer"] == "A社"


def test_missing_column_raises():
    df = pd.DataFrame({"customer": ["A社"], "month": ["2024-01"]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)
```

- [ ] **Step 2: テストが FAIL することを確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\02_manufacturing\20_customer_claim_monthly"
python -m pytest tests/test_analyze.py -v 2>&1 | head -10
```

期待: `ModuleNotFoundError` または `ImportError`

- [ ] **Step 3: `analyze.py` を作成（GREEN フェーズ）**

```python
"""顧客クレーム件数・原因分類 月次集計 — クレーム集計 + verdict ロジック。"""
from __future__ import annotations

import pandas as pd

REQUIRED_COLS = ["customer", "month", "category", "count"]


def _verdict(avg: float) -> str:
    if avg <= 5.0:
        return "good"
    elif avg <= 15.0:
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

    total_claims = int(data["count"].sum())
    n_months = int(data["month"].nunique())
    avg_monthly_claims = float(total_claims / n_months)

    category_totals = data.groupby("category")["count"].sum()
    top_category = str(category_totals.idxmax())

    customer_totals = data.groupby("customer")["count"].sum()
    worst_customer = str(customer_totals.idxmax())

    return {
        "result_df":          data,
        "total_claims":       total_claims,
        "avg_monthly_claims": avg_monthly_claims,
        "top_category":       top_category,
        "worst_customer":     worst_customer,
        "n_customers":        int(data["customer"].nunique()),
        "verdict":            _verdict(avg_monthly_claims),
    }
```

- [ ] **Step 4: 全テストが PASS することを確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\02_manufacturing\20_customer_claim_monthly"
python -m pytest tests/test_analyze.py -v
```

期待: `8 passed`

- [ ] **Step 5: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/20_customer_claim_monthly/analyze.py \
        02_manufacturing/20_customer_claim_monthly/tests/test_analyze.py
git commit -m "feat(C-74): analyze.py TDD — 8テスト all PASS（月次クレーム集計 + verdict）"
```

---

### Task 3: visualize.py

**Files:**
- Create: `02_manufacturing/20_customer_claim_monthly/visualize.py`

- [ ] **Step 1: `visualize.py` を作成**

```python
"""顧客クレーム件数・原因分類 月次集計 — Plotly チャート。"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

_NAVY  = "#1e3a5f"
_GREEN = "#16a34a"
_AMBER = "#d97706"
_RED   = "#dc2626"
_BG    = "#f5f7fa"

_PALETTE = [
    "#1e3a5f", "#16a34a", "#d97706", "#dc2626",
    "#7c3aed", "#0891b2", "#be185d", "#65a30d",
]


def claim_trend_chart(result_df: pd.DataFrame) -> go.Figure:
    """顧客 × 月ごとのクレーム件数グループ棒グラフ。"""
    customers = sorted(result_df["customer"].unique())
    months    = sorted(result_df["month"].unique())

    # 顧客 × 月の合計を pivot
    pivot = (
        result_df.groupby(["customer", "month"])["count"]
        .sum()
        .reset_index()
        .pivot(index="month", columns="customer", values="count")
        .reindex(months)
    )

    fig = go.Figure()
    for i, cust in enumerate(customers):
        fig.add_trace(go.Bar(
            x=months,
            y=pivot[cust].tolist() if cust in pivot.columns else [None] * len(months),
            name=cust,
            marker_color=_PALETTE[i % len(_PALETTE)],
        ))

    fig.add_hline(y=15.0, line_dash="dash", line_color=_RED,
                  annotation_text="15件（alert）", annotation_position="right")
    fig.add_hline(y=5.0, line_dash="dash", line_color=_GREEN,
                  annotation_text="5件（good）", annotation_position="right")
    fig.update_layout(
        barmode="group",
        title="顧客別 月次クレーム件数推移",
        xaxis_title="年月",
        yaxis_title="クレーム件数（件）",
        height=380,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25),
    )
    return fig


def category_chart(result_df: pd.DataFrame) -> go.Figure:
    """原因分類別 総クレーム件数 横棒グラフ（件数降順）。

    result_df must contain columns: category, count.
    """
    cat_totals = (
        result_df.groupby("category")["count"]
        .sum()
        .sort_values(ascending=True)  # 横棒は ascending=True で多い順が上
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=cat_totals.values,
        y=cat_totals.index,
        orientation="h",
        marker_color=_NAVY,
        text=[f"{int(v)}件" for v in cat_totals.values],
        textposition="outside",
    ))
    fig.update_layout(
        title="原因分類別 クレーム件数",
        xaxis=dict(title="クレーム件数（件）", range=[0, None]),
        yaxis_title="原因分類",
        height=320,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        showlegend=False,
    )
    return fig
```

- [ ] **Step 2: syntax + import チェック**

```bash
python -c "import ast; ast.parse(open('02_manufacturing/20_customer_claim_monthly/visualize.py', encoding='utf-8').read()); print('syntax OK')"
```

```bash
cd "02_manufacturing/20_customer_claim_monthly" && python -c "import visualize; print('import OK')"
```

期待: `syntax OK` → `import OK`

- [ ] **Step 3: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/20_customer_claim_monthly/visualize.py
git commit -m "feat(C-74): visualize.py — 月次トレンド棒グラフ + 原因分類横棒"
```

---

### Task 4: app.py + STATUS.md（production-ready）

**Files:**
- Create: `02_manufacturing/20_customer_claim_monthly/app.py`
- Modify: `02_manufacturing/20_customer_claim_monthly/STATUS.md`

- [ ] **Step 1: `app.py` を作成**

```python
"""顧客クレーム件数・原因分類 月次集計 — 月次クレーム集計 × 原因分類内訳。"""
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

st.set_page_config(page_title="顧客クレーム件数・原因分類 月次集計", page_icon="📋", layout="wide")

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
    "📋 顧客クレーム件数・原因分類 月次集計</h3>"
    "</div>",
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙ 設定")
    st.caption("CSV 列: customer / month / category / count")
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

# ── Main ──────────────────────────────────────────────────────────
if df is None:
    st.info("サイドバーから CSV をアップロードするか、「サンプルデータを使用」をクリックしてください。")
    st.stop()

if run_btn:
    try:
        result = analyze.run_analysis(df)
        st.session_state.update({
            "result":        result,
            "uploaded_name": uploaded.name if uploaded else "sample_customer_claim.csv",
            "row_count":     len(df),
        })
    except ValueError as e:
        st.error(str(e))
        st.stop()

    # DB書き込み（run_btn ガード内 — 分析実行時のみ）
    try:
        from _common.db_writer import init_db, write_upload, write_kpi
        init_db()
        uid = write_upload(
            "customer_claim_monthly",
            st.session_state.get("uploaded_name"),
            st.session_state.get("row_count"),
        )
        write_kpi(
            uid, "customer_claim_monthly",
            datetime.now().strftime("%Y-%m"),
            "claim_count",
            float(st.session_state["result"]["total_claims"]),
            st.session_state["result"]["verdict"],
        )
    except Exception as _e:
        st.caption(f"⚠ DB書き込みスキップ: {_e}")

result = st.session_state.get("result")
if not result:
    st.info("「▶ 分析実行」を押してください。")
    st.stop()

# ── KPI 4列 ────────────────────────────────────────────────────────
avg     = result["avg_monthly_claims"]
top_cat = result["top_category"]
verdict = result["verdict"]

_COLOR = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_LABEL = {"good": "クレーム少", "warning": "要注意", "alert": "要改善"}
v_color = _COLOR[verdict]
v_label = _LABEL[verdict]

c1, c2, c3, c4 = st.columns(4)
c1.metric("顧客数", f"{result['n_customers']}社")
c2.metric("月次平均クレーム数", f"{avg:.1f}件")
c3.metric("最多原因分類", top_cat)
c4.markdown(
    f'<div style="background:{v_color}22;border-left:4px solid {v_color};'
    f'padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{v_color};font-size:16px">{v_label}</b><br>'
    f'<span style="font-size:12px;color:#64748b">avg={avg:.1f}件/月</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# ── チャート ──────────────────────────────────────────────────────
col_l, col_r = st.columns([2, 1])
with col_l:
    st.plotly_chart(
        visualize.claim_trend_chart(result["result_df"]),
        use_container_width=True,
    )
with col_r:
    st.plotly_chart(
        visualize.category_chart(result["result_df"]),
        use_container_width=True,
    )

# ── テーブル ──────────────────────────────────────────────────────
st.subheader("クレームデータ詳細")
display_df = (
    result["result_df"][["customer", "month", "category", "count"]]
    .sort_values(["month", "customer", "category"])
    .reset_index(drop=True)
)
st.dataframe(display_df, use_container_width=True)
```

- [ ] **Step 2: `STATUS.md` を production-ready に更新**

```markdown
# C-74 顧客クレーム件数・原因分類 月次集計

- name: 顧客クレーム件数・原因分類 月次集計
- industry: 製造
- department: 品質保証
- status: production-ready
```

- [ ] **Step 3: syntax チェック**

```bash
python -c "import ast; ast.parse(open('02_manufacturing/20_customer_claim_monthly/app.py', encoding='utf-8').read()); print('OK')"
```

期待: `OK`

- [ ] **Step 4: 全テスト確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\02_manufacturing\20_customer_claim_monthly"
python -m pytest tests/test_analyze.py -v
```

期待: `8 passed`

- [ ] **Step 5: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/20_customer_claim_monthly/app.py \
        02_manufacturing/20_customer_claim_monthly/STATUS.md
git commit -m "feat(C-74): app.py + STATUS.md production-ready（月次クレーム集計 + 原因分類 + DB）"
```

---

### Task 5: dashboard.py + catalog.yml 更新

**Files:**
- Modify: `02_manufacturing/09_unified_dashboard/dashboard.py`（CARDS に追加）
- Modify: `catalog.yml`（C-74 エントリ追加）

- [ ] **Step 1: `dashboard.py` の CARDS リスト末尾に追加**

`02_manufacturing/09_unified_dashboard/dashboard.py` を Read して CARDS リストの末尾（`supplier_defect_rate` の行の直後）に以下を追加:

```python
    {"system_id": "customer_claim_monthly", "metric": "claim_count",
     "title": "月次クレーム総数", "fmt": lambda v: f"{int(v)}件"},
```

- [ ] **Step 2: `catalog.yml` の末尾に C-74 エントリを追記**

```yaml
- id: "C-74"
  name: "顧客クレーム件数・原因分類 月次集計"
  industry: "製造"
  department: "品質保証"
  difficulty: "★★★"
  status: "production-ready"
  priority: "A"
  path: "02_manufacturing/20_customer_claim_monthly"
  demo: "streamlit run 02_manufacturing/20_customer_claim_monthly/app.py"
  description: |
    顧客別・原因分類別のクレーム件数を CSV でアップロードし、月次推移と原因分類内訳を自動集計。
    月次平均クレーム数 ≤ 5件 → "good" の明快な verdict 設計。
    月次トレンドグラフと原因分類横棒グラフで改善ポイントを可視化。
```

- [ ] **Step 3: 全テスト確認**

```bash
python -m pytest 02_manufacturing/20_customer_claim_monthly/tests/ -v
```

期待: `8 passed`

- [ ] **Step 4: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/09_unified_dashboard/dashboard.py catalog.yml
git commit -m "feat(C-74): C-63ダッシュボード + catalog.yml に C-74 追加"
```

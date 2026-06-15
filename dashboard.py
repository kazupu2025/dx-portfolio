import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yaml
from pathlib import Path

st.set_page_config(
    page_title="DX ポートフォリオ",
    page_icon="📊",
    layout="wide",
)

ROOT = Path(__file__).parent

STATUS_LABELS = {
    "production-ready": "✅ Production-ready",
    "deployed":         "🚀 Deployed",
    "tested":           "🧪 Tested",
    "poc":              "🔧 PoC",
    "designing":        "📐 Designing",
    "idea":             "💡 Idea",
}
STATUS_COLORS = {
    "production-ready": "#22c55e",
    "deployed":         "#a855f7",
    "tested":           "#3b82f6",
    "poc":              "#f97316",
    "designing":        "#eab308",
    "idea":             "#64748b",
}
STATUS_RANK = {s: i for i, s in enumerate(STATUS_LABELS)}

INDUSTRY_ORDER = [
    "小売", "製造", "医療・介護", "金融・保険", "物流・倉庫",
    "飲食", "不動産", "人事・採用", "教育・研修", "サービス",
]
DEPT_ORDER = [
    "営業・販売", "経理・財務", "人事・労務",
    "物流・在庫", "生産・品質", "受付・CS", "購買・仕入",
]


@st.cache_data
def load_catalog() -> pd.DataFrame:
    with open(ROOT / "catalog.yml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    df = pd.DataFrame(data)
    df["id"] = df["id"].where(df["id"].notna(), other=None)
    df["path"] = df["path"].where(df["path"].notna(), other=None)
    df["demo"] = df["demo"].where(df["demo"].notna(), other=None)
    return df


def status_badge(status: str) -> str:
    label = STATUS_LABELS.get(status, status)
    color = STATUS_COLORS.get(status, "#64748b")
    return (
        f'<span style="background:{color};color:white;'
        f'padding:2px 10px;border-radius:12px;font-size:12px;font-weight:600">'
        f"{label}</span>"
    )


def build_matrix(df: pd.DataFrame) -> go.Figure:
    industries = [i for i in INDUSTRY_ORDER if i in df["industry"].values]
    depts = [d for d in DEPT_ORDER if d in df["department"].values]

    pivot = (
        df.pivot_table(index="industry", columns="department", aggfunc="size", fill_value=0)
        .reindex(index=industries, columns=depts, fill_value=0)
    )

    z = pivot.values.tolist()
    text_grid = [[str(v) if v > 0 else "" for v in row] for row in z]

    # Layer 1: Heatmap（見た目担当）
    fig = go.Figure(go.Heatmap(
        z=z,
        x=depts,
        y=industries,
        text=text_grid,
        texttemplate="%{text}",
        textfont={"size": 18, "color": "white"},
        colorscale=[[0, "#1e293b"], [0.001, "#1e3a5f"], [1, "#2563eb"]],
        showscale=False,
        xgap=3, ygap=3,
        hoverinfo="skip",
    ))

    # Layer 2: 透明 Scatter（クリックイベント担当）
    # Heatmap は on_select を発火しないため、同座標に不可視マーカーを重ねる
    x_pts, y_pts, hovers = [], [], []
    for ind in industries:
        for dept in depts:
            v = int(pivot.loc[ind, dept])
            x_pts.append(dept)
            y_pts.append(ind)
            hovers.append(f"<b>{ind} × {dept}</b><br>{v} 件")

    fig.add_trace(go.Scatter(
        x=x_pts, y=y_pts,
        mode="markers",
        marker=dict(size=48, color="rgba(0,0,0,0)", symbol="square"),
        hovertemplate="%{customdata}<extra></extra>",
        customdata=hovers,
        showlegend=False,
        selected=dict(marker=dict(color="rgba(96,165,250,0.35)", size=48)),
        unselected=dict(marker=dict(color="rgba(0,0,0,0)", size=48)),
    ))

    fig.update_layout(
        height=370,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        clickmode="event+select",
        xaxis=dict(
            side="bottom", tickfont=dict(size=13),
            categoryorder="array", categoryarray=depts,
        ),
        yaxis=dict(
            tickfont=dict(size=13),
            categoryorder="array", categoryarray=industries,
            autorange="reversed",
        ),
    )
    return fig


def main():
    st.title("📊 DX ポートフォリオ ダッシュボード")
    st.caption("業種 × 部署 別の DX 化ユースケース一覧")

    df = load_catalog()

    # ── メトリクスカード ──────────────────────────────
    counts = df["status"].value_counts()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("合計", len(df))
    c2.metric("✅ 完成", counts.get("production-ready", 0))
    c3.metric("🔧 開発中", sum(counts.get(s, 0) for s in ["poc", "designing", "tested"]))
    c4.metric("💡 アイデア", counts.get("idea", 0))
    c5.metric("🚀 稼働中", counts.get("deployed", 0))

    st.divider()

    # ── マトリクス ────────────────────────────────────
    st.subheader("業種 × 部署 マトリクス")
    st.caption("セルをクリックすると下のリストに絞り込まれます")
    event = st.plotly_chart(
        build_matrix(df),
        on_select="rerun",
        selection_mode="points",
        use_container_width=True,
    )

    # クリックイベントから業種・部署を取得（Scatter層 = curve_number 1 のみ）
    click_industry, click_dept = None, None
    if event and hasattr(event, "selection") and event.selection.points:
        for pt in event.selection.points:
            if pt.get("curve_number", 0) == 1:
                click_industry = pt.get("y")
                click_dept = pt.get("x")
                break

    st.divider()

    # ── フィルター ────────────────────────────────────
    st.subheader("タスクリスト")

    industry_opts = ["全業種"] + [i for i in INDUSTRY_ORDER if i in df["industry"].values]
    dept_opts = ["全部署"] + [d for d in DEPT_ORDER if d in df["department"].values]
    status_opts = ["全状態"] + [STATUS_LABELS[s] for s in STATUS_LABELS if s in df["status"].values]

    f1, f2, f3 = st.columns([2, 2, 2])
    sel_industry = f1.selectbox(
        "業種",
        industry_opts,
        index=industry_opts.index(click_industry) if click_industry in industry_opts else 0,
        key="sel_industry",
    )
    sel_dept = f2.selectbox(
        "部署",
        dept_opts,
        index=dept_opts.index(click_dept) if click_dept in dept_opts else 0,
        key="sel_dept",
    )
    sel_status_label = f3.selectbox("状態", status_opts, key="sel_status")

    # フィルタ適用
    mask = pd.Series(True, index=df.index)
    if sel_industry != "全業種":
        mask &= df["industry"] == sel_industry
    if sel_dept != "全部署":
        mask &= df["department"] == sel_dept
    if sel_status_label != "全状態":
        status_key = next((k for k, v in STATUS_LABELS.items() if v == sel_status_label), None)
        if status_key:
            mask &= df["status"] == status_key

    filtered = df[mask].copy()
    filtered["_rank"] = filtered["status"].map(STATUS_RANK).fillna(99)
    filtered = filtered.sort_values(["_rank", "industry", "name"]).drop(columns="_rank")

    st.caption(f"{len(filtered)} 件")

    # ── タスクカード ──────────────────────────────────
    for _, task in filtered.iterrows():
        with st.container(border=True):
            left, right = st.columns([3, 1])
            with left:
                task_id = task["id"] if pd.notna(task.get("id")) else None
                id_tag = f" `{task_id}`" if task_id else ""
                st.markdown(
                    f"{status_badge(task['status'])}{id_tag}　**{task['name']}**",
                    unsafe_allow_html=True,
                )
                st.caption(f"🏭 {task['industry']}　　🏢 {task['department']}")
                if task.get("description") and pd.notna(task.get("description")):
                    st.write(task["description"])
            with right:
                demo = task["demo"] if pd.notna(task.get("demo")) else None
                path = task["path"] if pd.notna(task.get("path")) else None
                if demo:
                    st.code(demo, language="bash")
                if path:
                    st.caption(f"📁 `{path}`")


if __name__ == "__main__":
    main()

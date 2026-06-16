"""
C-26: 請求書突合・差異検出パイプライン Streamlit ダッシュボード
"""
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="請求書突合ダッシュボード",
    page_icon="💰",
    layout="wide",
)

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"

STATUS_ORDER = ["一致", "差異", "過払", "未入金"]
STATUS_COLORS = {
    "一致": "green",
    "差異": "orange",
    "過払": "blue",
    "未入金": "red",
}


@st.cache_data
def load_data() -> pd.DataFrame:
    path = OUTPUT_DIR / "cleaned_invoice_202401.csv"
    df = pd.read_csv(path, encoding="utf-8-sig")
    for col in ["invoice_amount", "received_amount", "variance_amount", "variance_rate"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "invoice_date" in df.columns:
        df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
    return df


@st.cache_data
def load_report() -> str:
    p = OUTPUT_DIR / "analysis_report.md"
    return p.read_text(encoding="utf-8") if p.exists() else "レポートが見つかりません。"


def fmt_yen(val: float) -> str:
    """金額を日本円形式で表示（バックスラッシュY記号なし）"""
    return f"{val:,.0f} 円"


# --- データ読み込み ---
try:
    df_all = load_data()
except FileNotFoundError:
    st.error("cleaned_invoice_202401.csv が見つかりません。cleanse.py を先に実行してください。")
    st.stop()

report_text = load_report()

# --- タイトル ---
st.title("💰 金融・保険 請求書突合ダッシュボード")
st.caption("2024年1月 | C-26 請求書突合・差異検出パイプライン")

# --- 突合ステータスフィルター ---
available_statuses = [s for s in STATUS_ORDER if s in df_all["match_status"].unique()]
selected_statuses = st.multiselect(
    "突合ステータスフィルター",
    options=STATUS_ORDER,
    default=STATUS_ORDER,
)
df = df_all[df_all["match_status"].isin(selected_statuses)] if selected_statuses else df_all

# --- KPI 4つ ---
total_invoice = df["invoice_amount"].sum()
total_received = df["received_amount"].sum()
total_variance = df["variance_amount"].sum()
match_rate = (df["match_status"] == "一致").sum() / len(df) * 100 if len(df) > 0 else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("請求総額", fmt_yen(total_invoice))
c2.metric("入金総額", fmt_yen(total_received))
c3.metric(
    "差異総額",
    fmt_yen(total_variance),
    delta=f"{total_variance:+,.0f}",
    delta_color="inverse" if total_variance < 0 else "normal",
)
c4.metric(
    "一致率",
    f"{match_rate:.1f}%",
    delta="正常" if match_rate >= 80 else "要確認",
    delta_color="normal" if match_rate >= 80 else "inverse",
)

st.divider()

# --- 3タブ ---
tab1, tab2, tab3 = st.tabs(["突合状況", "得意先別差異", "支払区分分析"])

charts_dir = OUTPUT_DIR / "charts"

with tab1:
    st.subheader("突合ステータス別件数")
    p = charts_dir / "bar_match_status.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning("グラフなし。visualize.py を実行してください。")

    st.subheader("突合ステータス別サマリー")
    if "match_status" in df.columns:
        summary = df.groupby("match_status").agg(
            件数=("invoice_no", "count"),
            請求金額合計=("invoice_amount", "sum"),
            入金金額合計=("received_amount", "sum"),
            差異金額合計=("variance_amount", "sum"),
        ).reindex(STATUS_ORDER).fillna(0)
        summary["構成比(%)"] = (summary["件数"] / summary["件数"].sum() * 100).round(1)
        summary["請求金額合計"] = summary["請求金額合計"].map("{:,.0f}".format)
        summary["入金金額合計"] = summary["入金金額合計"].map("{:,.0f}".format)
        summary["差異金額合計"] = summary["差異金額合計"].map("{:,.0f}".format)
        st.dataframe(summary, use_container_width=True)

with tab2:
    st.subheader("差異金額上位10社")
    p = charts_dir / "bar_client_variance_top10.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning("グラフなし。visualize.py を実行してください。")

    st.subheader("差異明細テーブル")
    diff_df = df[df["match_status"] != "一致"].copy() if "match_status" in df.columns else df.copy()
    if len(diff_df) > 0:
        disp = diff_df[
            ["invoice_no", "client_code", "invoice_date", "invoice_amount",
             "received_amount", "variance_amount", "match_status", "payment_type"]
        ].sort_values("variance_amount", key=abs, ascending=False).head(100)
        st.dataframe(disp, use_container_width=True)
    else:
        st.info("差異なし。")

with tab3:
    st.subheader("支払区分別 件数")
    p = charts_dir / "pie_payment_type.png"
    if p.exists():
        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.image(str(p), use_container_width=True)
        with col_right:
            if "payment_type" in df.columns:
                pay_summary = df.groupby("payment_type").agg(
                    件数=("invoice_no", "count"),
                    差異件数=("match_status", lambda x: (x != "一致").sum()),
                    請求金額合計=("invoice_amount", "sum"),
                )
                pay_summary["差異発生率(%)"] = (
                    pay_summary["差異件数"] / pay_summary["件数"] * 100
                ).round(1)
                pay_summary["請求金額合計"] = pay_summary["請求金額合計"].map("{:,.0f}".format)
                st.dataframe(pay_summary, use_container_width=True)
    else:
        st.warning("グラフなし。visualize.py を実行してください。")

st.divider()

# --- 分析レポート expander ---
with st.expander("分析レポートを見る", expanded=False):
    st.markdown(report_text)

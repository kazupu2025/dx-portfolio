import streamlit as st
import pandas as pd
import json
from pathlib import Path
from analyze import analyze

# ページ設定
st.set_page_config(
    page_title="SaaSメトリクスダッシュボード",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 SaaSメトリクスダッシュボード")
st.markdown("MRR・チャーン率・LTV・CACなどの重要指標を月次で追跡・可視化")

# ====================
# サイドバー
# ====================
st.sidebar.header("📁 データ入力")

# サンプルデータの読み込み
sample_path = Path(__file__).parent / "sample_saas_metrics.csv"
sample_df = pd.read_csv(sample_path)

# CSVアップロード or サンプル使用
uploaded_file = st.sidebar.file_uploader(
    "CSVファイルをアップロード",
    type="csv",
    help="month, plan, new_customers, churned_customers, total_customers, mrr, new_mrr, churned_mrr, cac_spend を含む"
)

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.sidebar.success("✅ ファイルをアップロードしました")
else:
    df = sample_df.copy()
    st.sidebar.info("📌 サンプルデータを使用中")

# ====================
# 分析実行
# ====================
try:
    result = analyze(df)
except Exception as e:
    st.error(f"分析エラー: {e}")
    st.stop()

# ====================
# KPIカード
# ====================
st.header("📈 重要指標（KPI）")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="最新MRR",
        value=f"¥{result['latest_mrr']:,.0f}",
        delta=None
    )

with col2:
    st.metric(
        label="平均チャーン率",
        value=f"{result['avg_churn']:.1f}%",
        delta=None
    )

with col3:
    st.metric(
        label="平均CAC",
        value=f"¥{result['avg_cac']:,.0f}",
        delta=None
    )

with col4:
    st.metric(
        label="平均LTV",
        value=f"¥{result['avg_ltv']:,.0f}",
        delta=None
    )

# ====================
# 判定結果
# ====================
st.header("🎯 健全性診断")

col1, col2 = st.columns([2, 1])

with col1:
    verdict = result["verdict"]
    ratio = result["ltv_cac_ratio"]

    if verdict == "good":
        st.success(f"✅ **健全（LTV/CAC = {ratio:.2f}）**\nLTV/CAC比が3以上で、顧客生涯価値が高い")
    elif verdict == "warning":
        st.warning(f"⚠️ **要注意（LTV/CAC = {ratio:.2f}）**\nLTV/CAC比が1〜3で、改善の余地あり")
    else:
        st.error(f"❌ **危機状態（LTV/CAC = {ratio:.2f}）**\nLTV/CAC比が1未満で、CAC削減またはLTV向上が急務")

with col2:
    st.metric(
        label="LTV/CAC比",
        value=f"{ratio:.2f}",
        delta=None
    )

# ====================
# チャート
# ====================
st.header("📊 トレンド分析")

monthly_df = result["monthly_df"]

# MRR成長トレンド
col1, col2 = st.columns(2)

with col1:
    st.subheader("MRR推移（月次）")
    chart_data = monthly_df[["month", "total_mrr"]].copy()
    chart_data["month"] = chart_data["month"].dt.strftime("%Y-%m")
    st.line_chart(
        data=chart_data.set_index("month")["total_mrr"],
        use_container_width=True
    )

with col2:
    st.subheader("MRR成長率（%）")
    chart_data = monthly_df[["month", "mrr_growth_rate"]].copy()
    chart_data["month"] = chart_data["month"].dt.strftime("%Y-%m")
    # NaNをスキップしてプロット
    valid_data = chart_data[chart_data["mrr_growth_rate"].notna()]
    st.line_chart(
        data=valid_data.set_index("month")["mrr_growth_rate"],
        use_container_width=True
    )

# チャーン率トレンド
st.subheader("チャーン率トレンド（%）")
chart_data = monthly_df[["month", "churn_rate"]].copy()
chart_data["month"] = chart_data["month"].dt.strftime("%Y-%m")
st.line_chart(
    data=chart_data.set_index("month")["churn_rate"],
    use_container_width=True
)

# プラン別MRR構成
st.subheader("プラン別MRR分析")
plan_df = result["plan_df"]

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="プラン数",
        value=len(plan_df),
        delta=None
    )

with col2:
    st.metric(
        label="総解約顧客数",
        value=f"{int(plan_df['total_churned'].sum())}",
        delta=None
    )

# プラン別テーブル
st.dataframe(
    plan_df.rename(columns={
        "plan": "プラン",
        "avg_customers": "平均顧客数",
        "avg_mrr": "平均MRR",
        "total_churned": "総解約数"
    }),
    use_container_width=True
)

# ====================
# 月次データテーブル
# ====================
st.header("📋 月次データ詳細")

monthly_display = monthly_df.copy()
monthly_display["month"] = monthly_display["month"].dt.strftime("%Y-%m")

st.dataframe(
    monthly_display[[
        "month", "total_mrr", "new_mrr", "churned_mrr",
        "mrr_growth_rate", "total_customers", "churn_rate", "cac", "ltv"
    ]].rename(columns={
        "month": "月次",
        "total_mrr": "MRR",
        "new_mrr": "新規MRR",
        "churned_mrr": "解約MRR",
        "mrr_growth_rate": "成長率(%)",
        "total_customers": "顧客数",
        "churn_rate": "チャーン率(%)",
        "cac": "CAC",
        "ltv": "LTV"
    }),
    use_container_width=True
)

# ====================
# 分析結果のダウンロード
# ====================
st.header("💾 結果エクスポート")

# JSON形式でダウンロード
result_dict = {
    "latest_mrr": float(result["latest_mrr"]),
    "avg_churn": float(result["avg_churn"]),
    "avg_cac": float(result["avg_cac"]),
    "avg_ltv": float(result["avg_ltv"]),
    "ltv_cac_ratio": float(result["ltv_cac_ratio"]),
    "verdict": result["verdict"],
}

col1, col2 = st.columns(2)

with col1:
    json_str = json.dumps(result_dict, indent=2, ensure_ascii=False)
    st.download_button(
        label="📄 分析結果をJSONでダウンロード",
        data=json_str,
        file_name="analysis_result.json",
        mime="application/json"
    )

with col2:
    csv_str = monthly_display.to_csv(index=False)
    st.download_button(
        label="📊 月次データをCSVでダウンロード",
        data=csv_str,
        file_name="monthly_data.csv",
        mime="text/csv"
    )

# ====================
# フッター
# ====================
st.divider()
st.markdown(
    "**SaaSメトリクスダッシュボード v1.0** | "
    "MRR・チャーン・LTV・CACの総合分析"
)

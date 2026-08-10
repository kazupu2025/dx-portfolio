import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
# ── analyze.py インライン（Streamlit Cloud 互換）──
import pandas as pd
import numpy as np

REQUIRED_COLUMNS = ["customer_id", "company", "plan", "contract_start", "nps_score",
                    "login_days_30", "feature_usage_rate", "support_tickets", "onboarding_complete", "arr"]


def compute_health_score(row) -> float:
    """0-100のヘルススコア算出"""
    login_score = min(row["login_days_30"] / 20 * 40, 40)           # 20日以上で満点
    feature_score = row["feature_usage_rate"] * 30                   # 最大30点
    ticket_penalty = min(row["support_tickets"] * 2, 20)             # チケット多いほど減点
    onboarding_score = 10 if row["onboarding_complete"] else 0
    return max(0, login_score + feature_score - ticket_penalty + onboarding_score)


def analyze(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["contract_start"] = pd.to_datetime(df["contract_start"])
    df["health_score"] = df.apply(compute_health_score, axis=1)

    # NPS分類
    def nps_category(score):
        if score >= 9:
            return "Promoter"
        elif score >= 7:
            return "Passive"
        else:
            return "Detractor"

    # NPSスコアが-100〜100形式の場合は変換不要
    # NPS計算: (Promoter% - Detractor%) - ただしデータが-100~100なら平均を使用
    nps = float(df["nps_score"].mean())

    # ヘルススコア分布
    df["health_tier"] = pd.cut(df["health_score"], bins=[0, 40, 70, 100],
                                labels=["Risk", "Neutral", "Healthy"], include_lowest=True)

    risk_count = int((df["health_tier"] == "Risk").sum())
    healthy_count = int((df["health_tier"] == "Healthy").sum())
    at_risk_arr = float(df[df["health_tier"] == "Risk"]["arr"].sum())

    # プラン別
    plan_df = df.groupby("plan").agg(
        count=("customer_id", "count"),
        avg_health=("health_score", "mean"),
        avg_nps=("nps_score", "mean"),
        avg_login=("login_days_30", "mean"),
        total_arr=("arr", "sum"),
    ).reset_index().sort_values("avg_health", ascending=False)

    onboarding_rate = float(df["onboarding_complete"].mean() * 100)

    # 判定: healthy率 ≥60%→good, ≥40%→warning, <40%→alert
    healthy_rate = healthy_count / len(df) * 100
    if healthy_rate >= 60:
        verdict = "good"
    elif healthy_rate >= 40:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "df": df,
        "plan_df": plan_df,
        "nps": nps,
        "avg_health": float(df["health_score"].mean()),
        "risk_count": risk_count,
        "healthy_count": healthy_count,
        "at_risk_arr": at_risk_arr,
        "onboarding_rate": onboarding_rate,
        "healthy_rate": float(healthy_rate),
        "verdict": verdict,
    }

# ────────────────────────────────────────────────

BASE = Path(__file__).parent


@st.cache_data
def load_sample_data():
    return pd.read_csv(BASE / "sample_customer_success.csv")


st.title("📊 カスタマーサクセス指標ダッシュボード")
st.caption("NPS・ヘルススコア・オンボーディング・リスク分析")

# Sidebar
st.sidebar.header("📁 データ選択")
uploaded_file = st.sidebar.file_uploader("CSVファイルをアップロード", type=["csv"])

if st.sidebar.button("📊 サンプルデータを使用"):
    df_raw = load_sample_data()
else:
    df_raw = None

if uploaded_file:
    df_raw = pd.read_csv(uploaded_file)
elif df_raw is None:
    df_raw = load_sample_data()

# プランフィルタ
all_plans = sorted(df_raw["plan"].unique().tolist())
selected_plans = st.sidebar.multiselect("プランフィルター", all_plans, default=all_plans)
df_raw = df_raw[df_raw["plan"].isin(selected_plans)]

# 分析実行
result = analyze(df_raw)
df = result["df"]

# KPIカード 4つ
st.subheader("🎯 主要KPI")
c1, c2, c3, c4 = st.columns(4)

with c1:
    nps_value = result["nps"]
    st.metric(
        "平均 NPS",
        f"{nps_value:.1f}",
        delta="高評価" if nps_value > 50 else ("要注目" if nps_value > 0 else "改善要"))

with c2:
    health_value = result["avg_health"]
    st.metric(
        "平均ヘルススコア",
        f"{health_value:.1f}/100",
        delta="健全" if health_value >= 70 else ("注視中" if health_value >= 40 else "リスク"),
        delta_color="normal" if health_value >= 70 else ("off" if health_value >= 40 else "inverse"))

with c3:
    risk_value = result["risk_count"]
    st.metric(
        "リスク顧客数",
        f"{risk_value}",
        delta="要対応" if risk_value > 5 else "良好",
        delta_color="inverse" if risk_value > 5 else "normal")

with c4:
    verdict = result["verdict"]
    verdict_text = "好調 ✓" if verdict == "good" else ("要注意" if verdict == "warning" else "警告 ⚠")
    verdict_color = "green" if verdict == "good" else ("orange" if verdict == "warning" else "red")
    st.metric("総合判定", verdict_text)

st.divider()

# ヘルススコア分布ヒストグラム
st.subheader("📈 ヘルススコア分布")

health_counts = df["health_tier"].value_counts().to_dict()
risk_cnt = health_counts.get("Risk", 0)
neutral_cnt = health_counts.get("Neutral", 0)
healthy_cnt = health_counts.get("Healthy", 0)

col1, col2 = st.columns([2, 1])

with col1:
    chart_data = pd.DataFrame({
        "ステータス": ["Risk (0-40)", "Neutral (40-70)", "Healthy (70-100)"],
        "顧客数": [risk_cnt, neutral_cnt, healthy_cnt],
        "color": ["#ff4444", "#ffaa00", "#00aa00"]
    })
    st.bar_chart(data=chart_data.set_index("ステータス")["顧客数"])

with col2:
    st.write("**分布サマリー**")
    st.write(f"🔴 Risk: {risk_cnt}名 ({risk_cnt/len(df)*100:.1f}%)")
    st.write(f"🟡 Neutral: {neutral_cnt}名 ({neutral_cnt/len(df)*100:.1f}%)")
    st.write(f"🟢 Healthy: {healthy_cnt}名 ({healthy_cnt/len(df)*100:.1f}%)")

st.divider()

# プラン別ヘルスサマリー
st.subheader("📋 プラン別ヘルスサマリー")
plan_summary = result["plan_df"].copy()
plan_summary = plan_summary.rename(columns={
    "count": "顧客数",
    "avg_health": "平均ヘルススコア",
    "avg_nps": "平均NPS",
    "avg_login": "平均ログイン日数",
    "total_arr": "合計ARR"
})
plan_summary["平均ヘルススコア"] = plan_summary["平均ヘルススコア"].apply(lambda x: f"{x:.1f}")
plan_summary["平均NPS"] = plan_summary["平均NPS"].apply(lambda x: f"{x:.1f}")
plan_summary["平均ログイン日数"] = plan_summary["平均ログイン日数"].apply(lambda x: f"{x:.1f}")
plan_summary["合計ARR"] = plan_summary["合計ARR"].apply(lambda x: f"¥{x:,.0f}")

st.dataframe(plan_summary.reset_index(drop=True), use_container_width=True)

st.divider()

# リスク顧客一覧（トップ10）
st.subheader("🔴 リスク顧客一覧（ヘルススコア低い順 TOP 10）")
risk_df = df[df["health_tier"] == "Risk"].nsmallest(10, "health_score")[
    ["customer_id", "company", "plan", "health_score", "nps_score", "login_days_30", "arr"]
].copy()
risk_df = risk_df.rename(columns={
    "customer_id": "顧客ID",
    "company": "会社名",
    "plan": "プラン",
    "health_score": "ヘルススコア",
    "nps_score": "NPS",
    "login_days_30": "ログイン日数",
    "arr": "年間契約額"
})
risk_df["ヘルススコア"] = risk_df["ヘルススコア"].apply(lambda x: f"{x:.1f}")
risk_df["年間契約額"] = risk_df["年間契約額"].apply(lambda x: f"¥{x:,.0f}")

if len(risk_df) > 0:
    st.dataframe(risk_df, use_container_width=True)
else:
    st.success("✓ リスク顧客はいません")

st.divider()

# オンボーディング完了率ゲージ
st.subheader("🎓 オンボーディング完了率")
onboarding_rate = result["onboarding_rate"]
col1, col2 = st.columns([1, 2])

with col1:
    st.metric("完了率", f"{onboarding_rate:.1f}%")

with col2:
    st.progress(min(onboarding_rate / 100, 1.0))
    if onboarding_rate >= 80:
        st.success("✓ 高い完了率です")
    elif onboarding_rate >= 60:
        st.warning("△ 改善余地あり")
    else:
        st.error("⚠ オンボーディング強化が必要")

st.divider()

# 詳細分析テーブル
st.subheader("📊 全顧客詳細データ")
detail_df = df[[
    "customer_id", "company", "plan", "health_score", "health_tier",
    "nps_score", "login_days_30", "feature_usage_rate", "support_tickets",
    "onboarding_complete", "arr"
]].copy()
detail_df = detail_df.rename(columns={
    "customer_id": "顧客ID",
    "company": "会社名",
    "plan": "プラン",
    "health_score": "ヘルススコア",
    "health_tier": "ステータス",
    "nps_score": "NPS",
    "login_days_30": "ログイン日数",
    "feature_usage_rate": "機能使用率",
    "support_tickets": "サポートチケット数",
    "onboarding_complete": "オンボーディング完了",
    "arr": "年間契約額"
})
detail_df["ヘルススコア"] = detail_df["ヘルススコア"].apply(lambda x: f"{x:.1f}")
detail_df["機能使用率"] = detail_df["機能使用率"].apply(lambda x: f"{x:.1%}")
detail_df["年間契約額"] = detail_df["年間契約額"].apply(lambda x: f"¥{x:,.0f}")

st.dataframe(detail_df.sort_values("ヘルススコア", ascending=False), use_container_width=True)

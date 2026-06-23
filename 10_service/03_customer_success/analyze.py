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

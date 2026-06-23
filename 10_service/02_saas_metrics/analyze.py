import pandas as pd
import numpy as np

REQUIRED_COLUMNS = [
    "month", "plan", "new_customers", "churned_customers", "total_customers",
    "mrr", "new_mrr", "churned_mrr", "cac_spend"
]

def analyze(df: pd.DataFrame) -> dict:
    """
    SaaS指標を分析する。

    Args:
        df: 必須列を含むDataFrame

    Returns:
        月次集計、プラン別集計、KPI、判定を含む辞書
    """
    df = df.copy()
    df["month"] = pd.to_datetime(df["month"])

    # 月次合計
    monthly_df = df.groupby("month").agg(
        total_mrr=("mrr", "sum"),
        new_mrr=("new_mrr", "sum"),
        churned_mrr=("churned_mrr", "sum"),
        total_customers=("total_customers", "sum"),
        new_customers=("new_customers", "sum"),
        churned_customers=("churned_customers", "sum"),
        cac_spend=("cac_spend", "sum"),
    ).reset_index()

    # MRR成長率（月次）
    monthly_df["mrr_growth_rate"] = monthly_df["total_mrr"].pct_change() * 100

    # チャーン率（%）
    monthly_df["churn_rate"] = monthly_df["churned_customers"] / (
        monthly_df["total_customers"] + monthly_df["churned_customers"]
    ) * 100

    # CAC（1顧客獲得コスト）
    monthly_df["cac"] = monthly_df["cac_spend"] / monthly_df["new_customers"].replace(0, np.nan)

    # LTV（簡易計算: ARPU / churn_rate）
    monthly_df["arpu"] = monthly_df["total_mrr"] / monthly_df["total_customers"].replace(0, np.nan)
    monthly_df["ltv"] = monthly_df["arpu"] / (monthly_df["churn_rate"] / 100).replace(0, np.nan)

    # プラン別集計
    plan_df = df.groupby("plan").agg(
        avg_customers=("total_customers", "mean"),
        avg_mrr=("mrr", "mean"),
        total_churned=("churned_customers", "sum"),
    ).reset_index()

    # 最新月の指標
    latest = monthly_df.iloc[-1]
    latest_mrr = float(latest["total_mrr"])
    avg_churn = float(monthly_df["churn_rate"].mean())
    latest_cac = float(monthly_df["cac"].mean())
    latest_ltv = float(monthly_df["ltv"].mean())
    ltv_cac_ratio = latest_ltv / latest_cac if latest_cac > 0 else 0

    # 判定: LTV/CAC ≥3→good, ≥1→warning, <1→alert
    if ltv_cac_ratio >= 3:
        verdict = "good"
    elif ltv_cac_ratio >= 1:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "monthly_df": monthly_df,
        "plan_df": plan_df,
        "latest_mrr": latest_mrr,
        "avg_churn": avg_churn,
        "avg_cac": latest_cac,
        "avg_ltv": latest_ltv,
        "ltv_cac_ratio": float(ltv_cac_ratio),
        "verdict": verdict,
    }

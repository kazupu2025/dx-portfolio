import pandas as pd

REQUIRED_COLUMNS = [
    "date", "event_type", "room_name", "guests", "food_revenue",
    "beverage_revenue", "room_fee", "total_revenue", "status"
]


def analyze(df: pd.DataFrame) -> dict:
    """
    宴会・イベント収益分析を実行する
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df_comp = df[df["status"] == "完了"]

    # KPI計算
    total_revenue = float(df_comp["total_revenue"].sum())
    total_events = int(len(df_comp))
    avg_revenue_per_event = (
        float(df_comp["total_revenue"].mean()) if total_events > 0 else 0
    )
    avg_revenue_per_guest = (
        float((df_comp["total_revenue"] / df_comp["guests"].replace(0, 1)).mean())
        if total_events > 0
        else 0
    )

    # イベント種別分析
    event_df = (
        df_comp.groupby("event_type")
        .agg(
            count=("date", "count"),
            total_revenue=("total_revenue", "sum"),
            avg_revenue=("total_revenue", "mean"),
            avg_guests=("guests", "mean"),
        )
        .reset_index()
        .sort_values("total_revenue", ascending=False)
    )

    # 会場別分析
    room_df = (
        df_comp.groupby("room_name")
        .agg(
            count=("date", "count"),
            total_revenue=("total_revenue", "sum"),
            avg_guests=("guests", "mean"),
        )
        .reset_index()
        .sort_values("total_revenue", ascending=False)
    )

    # 月次トレンド
    monthly_df = (
        df_comp.groupby(df_comp["date"].dt.to_period("M"))
        .agg(
            total_revenue=("total_revenue", "sum"),
            count=("date", "count"),
        )
        .reset_index()
    )
    monthly_df["date"] = monthly_df["date"].astype(str)

    # キャンセル率
    cancel_rate = float((df["status"] == "キャンセル").sum() / len(df) * 100)

    # 判定
    if avg_revenue_per_guest >= 15000:
        verdict = "good"
    elif avg_revenue_per_guest >= 8000:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "df": df_comp,
        "event_df": event_df,
        "room_df": room_df,
        "monthly_df": monthly_df,
        "total_revenue": total_revenue,
        "total_events": total_events,
        "avg_revenue_per_event": avg_revenue_per_event,
        "avg_revenue_per_guest": avg_revenue_per_guest,
        "cancel_rate": cancel_rate,
        "verdict": verdict,
    }

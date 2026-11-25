import pandas as pd

REQUIRED_COLUMNS = ["date","staff_name","role","start_time","end_time","hourly_rate","break_minutes"]

def analyze(df: pd.DataFrame, monthly_sales: float = 1500000.0) -> dict:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # 実働時間計算
    def calc_hours(row):
        s = pd.to_datetime(row["start_time"], format="%H:%M")
        e = pd.to_datetime(row["end_time"], format="%H:%M")
        total_min = (e - s).seconds / 60
        return max(0, total_min - row["break_minutes"]) / 60

    df["work_hours"] = df.apply(calc_hours, axis=1)
    df["cost"] = df["work_hours"] * df["hourly_rate"]

    # 合計
    total_cost = df["cost"].sum()
    total_hours = df["work_hours"].sum()
    labor_ratio = total_cost / monthly_sales * 100  # 人件費率(%)

    # スタッフ別
    staff_df = df.groupby("staff_name").agg(
        total_hours=("work_hours", "sum"),
        total_cost=("cost", "sum"),
        shift_count=("date", "count"),
    ).reset_index().sort_values("total_cost", ascending=False)

    # 役割別
    role_df = df.groupby("role").agg(
        total_hours=("work_hours", "sum"),
        total_cost=("cost", "sum"),
    ).reset_index()

    # 日次コスト
    daily_df = df.groupby("date")["cost"].sum().reset_index(name="daily_cost")

    # 判定: 人件費率 ≤25%→good, ≤35%→warning, >35%→alert
    if labor_ratio <= 25:
        verdict = "good"
    elif labor_ratio <= 35:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "df": df,
        "staff_df": staff_df,
        "role_df": role_df,
        "daily_df": daily_df,
        "total_cost": float(total_cost),
        "total_hours": float(total_hours),
        "labor_ratio": float(labor_ratio),
        "monthly_sales": float(monthly_sales),
        "verdict": verdict,
    }

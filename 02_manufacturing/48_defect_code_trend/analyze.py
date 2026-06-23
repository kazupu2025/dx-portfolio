import pandas as pd

REQUIRED_COLUMNS = ["date", "process", "defect_code", "count"]

def analyze(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)

    code_df = df.groupby("defect_code")["count"].sum().reset_index().sort_values("count", ascending=False)
    total_defects = code_df["count"].sum()
    code_df["pct"] = code_df["count"] / total_defects * 100

    process_df = df.groupby("process")["count"].sum().reset_index().sort_values("count", ascending=False)

    trend_df = df.groupby(["month", "defect_code"])["count"].sum().reset_index()

    top_code = code_df.iloc[0]["defect_code"]
    top_code_pct = float(code_df.iloc[0]["pct"])

    if top_code_pct <= 30:
        verdict = "good"
    elif top_code_pct <= 50:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "code_df": code_df,
        "process_df": process_df,
        "trend_df": trend_df,
        "total_defects": int(total_defects),
        "top_code": top_code,
        "top_code_pct": top_code_pct,
        "verdict": verdict,
    }

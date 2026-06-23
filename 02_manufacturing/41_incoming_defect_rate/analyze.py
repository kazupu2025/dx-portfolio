import pandas as pd

REQUIRED_COLUMNS = ["date", "supplier", "inspection_count", "defect_count"]

def analyze(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["defect_rate"] = df["defect_count"] / df["inspection_count"] * 100

    supplier_df = df.groupby("supplier").agg(
        total_inspection=("inspection_count", "sum"),
        total_defect=("defect_count", "sum"),
    ).reset_index()
    supplier_df["defect_rate"] = supplier_df["total_defect"] / supplier_df["total_inspection"] * 100

    df["month"] = df["date"].dt.to_period("M").astype(str)
    trend_df = df.groupby("month").agg(
        total_inspection=("inspection_count", "sum"),
        total_defect=("defect_count", "sum"),
    ).reset_index()
    trend_df["defect_rate"] = trend_df["total_defect"] / trend_df["total_inspection"] * 100

    avg_defect_rate = supplier_df["defect_rate"].mean()

    if avg_defect_rate <= 1.0:
        verdict = "good"
    elif avg_defect_rate <= 3.0:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "supplier_df": supplier_df,
        "trend_df": trend_df,
        "avg_defect_rate": avg_defect_rate,
        "worst_supplier": supplier_df.loc[supplier_df["defect_rate"].idxmax(), "supplier"],
        "verdict": verdict,
    }

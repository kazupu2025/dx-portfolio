import pandas as pd

REQUIRED_COLUMNS = ["date", "inspector", "inspected", "defects_found", "true_defects"]

def analyze(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["detection_rate"] = df["defects_found"] / df["true_defects"].clip(lower=1) * 100
    df["miss_count"] = df["true_defects"] - df["defects_found"]

    inspector_df = df.groupby("inspector").agg(
        total_inspected=("inspected", "sum"),
        total_found=("defects_found", "sum"),
        total_true=("true_defects", "sum"),
        avg_detection_rate=("detection_rate", "mean"),
    ).reset_index()
    inspector_df["detection_rate"] = inspector_df["total_found"] / inspector_df["total_true"].clip(lower=1) * 100

    avg_detection_rate = float(inspector_df["detection_rate"].mean())
    worst_inspector = inspector_df.loc[inspector_df["detection_rate"].idxmin(), "inspector"]

    if avg_detection_rate >= 95:
        verdict = "good"
    elif avg_detection_rate >= 85:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "inspector_df": inspector_df,
        "avg_detection_rate": avg_detection_rate,
        "worst_inspector": worst_inspector,
        "total_miss": int(df["miss_count"].sum()),
        "verdict": verdict,
    }

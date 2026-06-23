import pandas as pd
import numpy as np

# SPC定数 (d2, D3, D4 for subgroup sizes)
SPC_CONSTANTS = {
    2: {"d2": 1.128, "D3": 0, "D4": 3.267, "A2": 1.880},
    3: {"d2": 1.693, "D3": 0, "D4": 2.574, "A2": 1.023},
    4: {"d2": 2.059, "D3": 0, "D4": 2.282, "A2": 0.729},
    5: {"d2": 2.326, "D3": 0, "D4": 2.114, "A2": 0.577},
}

def compute_control_limits(df: pd.DataFrame, subgroup_size: int = 5) -> dict:
    """
    df columns: subgroup_id, value
    Returns X-bar/R chart data with control limits.
    """
    df = df.copy()
    grouped = df.groupby("subgroup_id")["value"]
    xbar = grouped.mean().reset_index(name="xbar")
    rng = grouped.apply(lambda x: x.max() - x.min()).reset_index(name="r")
    sg_df = pd.merge(xbar, rng, on="subgroup_id")

    const = SPC_CONSTANTS.get(subgroup_size, SPC_CONSTANTS[5])
    xbar_bar = sg_df["xbar"].mean()
    r_bar = sg_df["r"].mean()

    ucl_x = xbar_bar + const["A2"] * r_bar
    lcl_x = xbar_bar - const["A2"] * r_bar
    ucl_r = const["D4"] * r_bar
    lcl_r = const["D3"] * r_bar

    return {
        "sg_df": sg_df,
        "xbar_bar": float(xbar_bar),
        "r_bar": float(r_bar),
        "ucl_x": float(ucl_x),
        "lcl_x": float(lcl_x),
        "ucl_r": float(ucl_r),
        "lcl_r": float(lcl_r),
    }

def detect_violations(sg_df: pd.DataFrame, ucl_x: float, lcl_x: float) -> list:
    """Rule 1: point outside control limits."""
    violations = []
    for _, row in sg_df.iterrows():
        if row["xbar"] > ucl_x or row["xbar"] < lcl_x:
            violations.append(int(row["subgroup_id"]))
    return violations

def analyze(df: pd.DataFrame, subgroup_size: int = 5) -> dict:
    limits = compute_control_limits(df, subgroup_size)
    violations = detect_violations(limits["sg_df"], limits["ucl_x"], limits["lcl_x"])
    n_violations = len(violations)

    if n_violations == 0:
        verdict = "good"
    elif n_violations <= 2:
        verdict = "warning"
    else:
        verdict = "alert"

    return {**limits, "violations": violations, "n_violations": n_violations, "verdict": verdict}

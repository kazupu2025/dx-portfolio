import pandas as pd
import numpy as np
from pathlib import Path

REQUIRED_SERVICE_COLUMNS = ["date","job_id","customer","vehicle_type","service_type","labor_hours","parts_cost","labor_rate","status"]
REQUIRED_PARTS_COLUMNS = ["part_id","part_name","category","current_stock","min_stock","unit_cost","supplier"]

def analyze(service_df: pd.DataFrame, parts_df: pd.DataFrame) -> dict:
    service_df = service_df.copy()
    parts_df = parts_df.copy()

    service_df["date"] = pd.to_datetime(service_df["date"])
    service_df["labor_cost"] = service_df["labor_hours"] * service_df["labor_rate"]
    service_df["total_revenue"] = service_df["labor_cost"] + service_df["parts_cost"]

    # 整備タイプ別集計
    service_type_df = service_df.groupby("service_type").agg(
        count=("job_id","count"),
        avg_hours=("labor_hours","mean"),
        avg_revenue=("total_revenue","mean"),
        total_revenue=("total_revenue","sum"),
    ).reset_index().sort_values("total_revenue", ascending=False)

    # 車種別集計
    vehicle_df = service_df.groupby("vehicle_type").agg(
        count=("job_id","count"),
        avg_revenue=("total_revenue","mean"),
    ).reset_index()

    # 月次売上
    monthly_df = service_df.groupby(service_df["date"].dt.to_period("M")).agg(
        total_revenue=("total_revenue","sum"),
        job_count=("job_id","count"),
    ).reset_index()
    monthly_df["date"] = monthly_df["date"].astype(str)

    # 部品在庫アラート
    parts_df["stock_ratio"] = parts_df["current_stock"] / parts_df["min_stock"]
    parts_df["alert"] = parts_df["current_stock"] < parts_df["min_stock"]
    alert_parts = parts_df[parts_df["alert"]].sort_values("stock_ratio")

    total_revenue = float(service_df["total_revenue"].sum())
    completed_jobs = int((service_df["status"] == "完了").sum())
    completion_rate = completed_jobs / len(service_df) * 100
    stock_alert_count = int(parts_df["alert"].sum())

    # 判定: 案件完了率 ≥80% かつ 在庫アラート ≤2→good, 完了率≥60%→warning, それ以外→alert
    if completion_rate >= 80 and stock_alert_count <= 2:
        verdict = "good"
    elif completion_rate >= 60:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "service_df": service_df,
        "service_type_df": service_type_df,
        "vehicle_df": vehicle_df,
        "monthly_df": monthly_df,
        "parts_df": parts_df,
        "alert_parts": alert_parts,
        "total_revenue": total_revenue,
        "completion_rate": float(completion_rate),
        "stock_alert_count": stock_alert_count,
        "verdict": verdict,
    }

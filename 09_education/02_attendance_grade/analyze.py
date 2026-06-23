#!/usr/bin/env python3
"""
C-112 Attendance & Grade Analysis Module
Analyzes attendance rates, average scores, and student performance across classes and subjects.
"""
import pandas as pd
import numpy as np

REQUIRED_COLUMNS = ["month", "class_name", "subject", "attendance_rate", "avg_score", "student_count", "failing_count"]


def analyze(df: pd.DataFrame) -> dict:
    """
    Analyze attendance and grade data.

    Args:
        df: DataFrame with required columns

    Returns:
        Dictionary with analysis results including:
        - df: Processed dataframe with failing_rate column
        - class_df: Class-level aggregation
        - subject_df: Subject-level aggregation
        - trend_df: Monthly trend
        - overall_attendance: Overall average attendance rate
        - overall_score: Overall average score
        - overall_failing_rate: Overall average failing rate
        - correlation: Correlation between attendance and score
        - alert_classes: List of classes requiring attention
        - verdict: Overall status (good/warning/alert)
    """
    df = df.copy()

    # Calculate failing rate
    df["failing_rate"] = df["failing_count"] / df["student_count"] * 100

    # Overall metrics
    overall_attendance = df["attendance_rate"].mean()
    overall_score = df["avg_score"].mean()
    overall_failing_rate = df["failing_rate"].mean()

    # Class-level aggregation
    class_df = df.groupby("class_name").agg(
        avg_attendance=("attendance_rate", "mean"),
        avg_score=("avg_score", "mean"),
        avg_failing_rate=("failing_rate", "mean"),
        total_students=("student_count", "mean"),
    ).reset_index().sort_values("avg_score", ascending=False)

    # Subject-level aggregation
    subject_df = df.groupby("subject").agg(
        avg_attendance=("attendance_rate", "mean"),
        avg_score=("avg_score", "mean"),
        avg_failing_rate=("failing_rate", "mean"),
    ).reset_index().sort_values("avg_score", ascending=False)

    # Monthly trend
    trend_df = df.groupby("month").agg(
        avg_attendance=("attendance_rate", "mean"),
        avg_score=("avg_score", "mean"),
    ).reset_index()

    # Correlation between attendance and score
    correlation = float(df["attendance_rate"].corr(df["avg_score"]))

    # Alert classes: attendance < 85% OR average score < 60
    alert_classes = class_df[
        (class_df["avg_attendance"] < 85) | (class_df["avg_score"] < 60)
    ]["class_name"].tolist()

    # Verdict based on overall attendance
    if overall_attendance >= 90:
        verdict = "good"
    elif overall_attendance >= 80:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "df": df,
        "class_df": class_df,
        "subject_df": subject_df,
        "trend_df": trend_df,
        "overall_attendance": float(overall_attendance),
        "overall_score": float(overall_score),
        "overall_failing_rate": float(overall_failing_rate),
        "correlation": correlation,
        "alert_classes": alert_classes,
        "verdict": verdict,
    }

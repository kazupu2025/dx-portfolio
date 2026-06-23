#!/usr/bin/env python3
"""
Sample data generator for C-112 attendance and grade report
Generates 48 rows: 6 months × 4 classes × 2 subjects (reduced for clarity)
"""
import pandas as pd
import numpy as np
from pathlib import Path

def generate_sample_data():
    """Generate realistic sample data with class-specific characteristics"""
    np.random.seed(42)
    rng = np.random.default_rng(42)

    months = [f"2024-{m:02d}" for m in range(4, 10)]  # Apr-Sep (6 months)
    classes = ["A組", "B組", "C組", "D組"]
    subjects = ["数学", "英語", "理科", "社会", "国語"]

    rows = []

    for month in months:
        for class_name in classes:
            for subject in subjects:
                # Class-specific characteristics
                if class_name == "A組":
                    # A: High attendance, good grades
                    attendance = rng.normal(92, 2)
                    avg_score = rng.normal(78, 4)
                    failing_count = max(0, int(rng.normal(1, 1)))
                elif class_name == "D組":
                    # D: Low attendance, poor grades
                    attendance = rng.normal(80, 3)
                    avg_score = rng.normal(62, 6)
                    failing_count = max(0, int(rng.normal(5, 2)))
                else:
                    # B, C: Mid-range
                    attendance = rng.normal(86, 2.5)
                    avg_score = rng.normal(70, 5)
                    failing_count = max(0, int(rng.normal(2.5, 1.5)))

                # Clamp values to realistic ranges
                attendance = max(75.0, min(98.0, attendance))
                avg_score = max(55.0, min(85.0, avg_score))
                student_count = rng.integers(28, 36)
                failing_count = min(failing_count, student_count // 3)  # At most 1/3 failing

                rows.append({
                    "month": month,
                    "class_name": class_name,
                    "subject": subject,
                    "attendance_rate": round(attendance, 1),
                    "avg_score": round(avg_score, 1),
                    "student_count": int(student_count),
                    "failing_count": int(failing_count),
                })

    df = pd.DataFrame(rows)
    return df

if __name__ == "__main__":
    df = generate_sample_data()
    output_path = Path(__file__).parent / "sample_attendance_grade.csv"
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"Generated {len(df)} rows -> {output_path}")
    print(df.head(10))

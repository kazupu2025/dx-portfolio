"""データクレンジング: 3スタイルCSVを統一フォーマットに変換"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COLUMN_MAP = {
    # work_date
    "作業日": "work_date", "WorkDate": "work_date", "日付": "work_date",
    # worker_id
    "作業員ID": "worker_id", "WorkerID": "worker_id", "従業員番号": "worker_id",
    # line
    "ライン": "line", "Line": "line", "製造ライン": "line",
    # process
    "工程": "process", "Process": "process", "作業区分": "process",
    # production_qty
    "生産数量": "production_qty", "ProductionQty": "production_qty", "生産実績": "production_qty",
    # defect_qty
    "不良数": "defect_qty", "DefectQty": "defect_qty", "不良品数": "defect_qty",
    # work_hours
    "作業時間": "work_hours", "WorkHours": "work_hours", "稼働時間": "work_hours",
    # overtime_hours
    "残業時間": "overtime_hours", "OvertimeHours": "overtime_hours", "残業": "overtime_hours",
}

NUMERIC_COLS = ["production_qty", "defect_qty", "work_hours", "overtime_hours"]

dfs = []
for csv_file in sorted(DATA_DIR.glob("*.csv")):
    df = pd.read_csv(csv_file, encoding="utf-8-sig")
    df = df.rename(columns=COLUMN_MAP)
    df["source_file"] = csv_file.name
    dfs.append(df)

merged = pd.concat(dfs, ignore_index=True)

# Normalize date to YYYY-MM-DD (unify / and - separators before parsing)
merged["work_date"] = merged["work_date"].astype(str).str.replace("/", "-", regex=False)
merged["work_date"] = pd.to_datetime(merged["work_date"], errors="coerce", format="%Y-%m-%d").dt.strftime("%Y-%m-%d")

# Coerce numeric columns
for col in NUMERIC_COLS:
    if col in merged.columns:
        merged[col] = pd.to_numeric(merged[col], errors="coerce")
        merged[col] = merged[col].fillna(merged[col].median())

# Computed columns
merged["defect_rate"] = np.where(
    merged["production_qty"] > 0,
    merged["defect_qty"] / merged["production_qty"],
    np.nan,
)

merged["productivity"] = np.where(
    merged["work_hours"] > 0,
    merged["production_qty"] / merged["work_hours"],
    np.nan,
)

productivity_median = merged["productivity"].median()
merged["performance_flag"] = merged["productivity"].apply(
    lambda x: "高生産性" if (pd.notna(x) and x > productivity_median) else "低生産性"
)

CANONICAL_COLS = [
    "work_date", "worker_id", "line", "process",
    "production_qty", "defect_qty", "work_hours", "overtime_hours",
    "defect_rate", "productivity", "performance_flag", "source_file",
]
out_cols = [c for c in CANONICAL_COLS if c in merged.columns]
out_path = OUTPUT_DIR / "cleaned_worker_202401.csv"
merged[out_cols].to_csv(out_path, index=False, encoding="utf-8-sig")
print(f"クレンジング完了: {len(merged)}行 -> {out_path}")

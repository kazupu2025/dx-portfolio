"""データクレンジング: 3スタイルCSVを統一フォーマットに変換"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COLUMN_MAP = {
    "製品ID": "product_id", "product_id": "product_id", "品番": "product_id",
    "製品名": "product_name", "product_name": "product_name", "品目": "product_name",
    "製造日": "production_date", "production_date": "production_date", "生産日": "production_date",
    "ラインID": "line_id", "line_id": "line_id", "製造ライン": "line_id",
    "計画数量": "planned_qty", "planned_qty": "planned_qty", "計画生産数": "planned_qty",
    "実績数量": "actual_qty", "actual_qty": "actual_qty", "実績生産数": "actual_qty",
    "計画材料費": "planned_material", "planned_material": "planned_material", "材料費予算": "planned_material",
    "実績材料費": "actual_material", "actual_material": "actual_material", "材料費実績": "actual_material",
    "計画労務費": "planned_labor", "planned_labor": "planned_labor", "労務費予算": "planned_labor",
    "実績労務費": "actual_labor", "actual_labor": "actual_labor", "労務費実績": "actual_labor",
    "計画間接費": "planned_overhead", "planned_overhead": "planned_overhead", "製造間接費予算": "planned_overhead",
    "実績間接費": "actual_overhead", "actual_overhead": "actual_overhead", "製造間接費実績": "actual_overhead",
}

NUMERIC_COLS = ["planned_qty","actual_qty","planned_material","actual_material",
                "planned_labor","actual_labor","planned_overhead","actual_overhead"]

dfs = []
for csv_file in sorted(DATA_DIR.glob("*.csv")):
    df = pd.read_csv(csv_file, encoding="utf-8-sig")
    df = df.rename(columns=COLUMN_MAP)
    df["source_file"] = csv_file.name
    dfs.append(df)

merged = pd.concat(dfs, ignore_index=True)

# Normalize date
merged["production_date"] = pd.to_datetime(merged["production_date"], errors="coerce").dt.strftime("%Y-%m-%d")

# Fill missing numerics with median
for col in NUMERIC_COLS:
    if col in merged.columns:
        merged[col] = pd.to_numeric(merged[col], errors="coerce")
        merged[col] = merged[col].fillna(merged[col].median())

# Variance calculations
merged["material_variance"] = merged["actual_material"] - merged["planned_material"]
merged["labor_variance"] = merged["actual_labor"] - merged["planned_labor"]
merged["overhead_variance"] = merged["actual_overhead"] - merged["planned_overhead"]
merged["planned_total_cost"] = merged["planned_material"] + merged["planned_labor"] + merged["planned_overhead"]
merged["actual_total_cost"] = merged["actual_material"] + merged["actual_labor"] + merged["actual_overhead"]
merged["total_variance"] = merged["actual_total_cost"] - merged["planned_total_cost"]
merged["variance_ratio"] = merged["total_variance"] / merged["planned_total_cost"]
merged["qty_variance"] = merged["actual_qty"] - merged["planned_qty"]

def flag(r):
    if r["variance_ratio"] > 0.10:
        return "超過"
    elif r["variance_ratio"] < -0.10:
        return "節約"
    else:
        return "正常"

merged["variance_flag"] = merged.apply(flag, axis=1)

out_path = OUTPUT_DIR / "cleaned_production_cost_202401.csv"
merged.to_csv(out_path, index=False, encoding="utf-8-sig")
print(f"クレンジング完了: {len(merged)}行 → {out_path}")

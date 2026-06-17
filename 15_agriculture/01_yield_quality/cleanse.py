# -*- coding: utf-8 -*-
"""
C-49 作物収量・品質検査レポートパイプライン
データクレンジングスクリプト
"""

import os
import pandas as pd
import numpy as np

random_import_guard = None  # no random needed here

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Column mapping for 3 styles ---
COLUMN_MAP = {
    # StyleA
    "収穫日": "harvest_date",
    "記録ID": "record_id",
    "農場ID": "farm_id",
    "農場名": "farm_name",
    "作物名": "crop",
    "収穫量(kg)": "harvest_qty",
    "A等級数量": "grade_a_qty",
    "不合格数量": "defect_qty",
    "検査員ID": "inspector_id",
    # StyleB
    "HarvestDate": "harvest_date",
    "RecordID": "record_id",
    "FarmID": "farm_id",
    "FarmName": "farm_name",
    "Crop": "crop",
    "HarvestQty": "harvest_qty",
    "GradeAQty": "grade_a_qty",
    "DefectQty": "defect_qty",
    "InspectorID": "inspector_id",
    # StyleC
    "出荷日": "harvest_date",
    "レコード番号": "record_id",
    "圃場ID": "farm_id",
    "圃場名": "farm_name",
    "品目": "crop",
    "収量kg": "harvest_qty",
    "A品数量": "grade_a_qty",
    "不良数量": "defect_qty",
    "担当検査員": "inspector_id",
}

CANONICAL_COLS = [
    "harvest_date",
    "record_id",
    "farm_id",
    "farm_name",
    "crop",
    "harvest_qty",
    "grade_a_qty",
    "defect_qty",
    "inspector_id",
    "grade_a_rate",
    "defect_rate",
    "quality_flag",
    "source_file",
]


def load_and_rename(filepath):
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    df = df.rename(columns=COLUMN_MAP)
    df["source_file"] = os.path.basename(filepath)
    return df


def normalize_date(series):
    return pd.to_datetime(
        series.astype(str).str.replace("/", "-"),
        format="%Y-%m-%d",
        errors="coerce",
    ).dt.strftime("%Y-%m-%d")


def compute_derived(df):
    df["harvest_qty"] = pd.to_numeric(df["harvest_qty"], errors="coerce")
    df["grade_a_qty"] = pd.to_numeric(df["grade_a_qty"], errors="coerce")
    df["defect_qty"] = pd.to_numeric(df["defect_qty"], errors="coerce")

    mask = df["harvest_qty"] > 0
    df["grade_a_rate"] = np.where(
        mask, df["grade_a_qty"] / df["harvest_qty"], np.nan
    )
    df["defect_rate"] = np.where(
        mask, df["defect_qty"] / df["harvest_qty"], np.nan
    )

    def quality_flag(r):
        if pd.isna(r):
            return "要改善"
        if r >= 0.8:
            return "優良"
        if r >= 0.6:
            return "合格"
        return "要改善"

    df["quality_flag"] = df["grade_a_rate"].apply(quality_flag)
    return df


def main():
    files = [
        os.path.join(DATA_DIR, "harvest_styleA.csv"),
        os.path.join(DATA_DIR, "harvest_styleB.csv"),
        os.path.join(DATA_DIR, "harvest_styleC.csv"),
    ]

    dfs = []
    for f in files:
        df = load_and_rename(f)
        df["harvest_date"] = normalize_date(df["harvest_date"])
        df = compute_derived(df)
        dfs.append(df)
        print(f"[OK] Loaded {os.path.basename(f)}: {len(df)} rows")

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined[CANONICAL_COLS]

    out_path = os.path.join(OUTPUT_DIR, "cleaned_harvest_202401.csv")
    combined.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[OK] Cleaned data saved: {out_path} ({len(combined)} rows)")


if __name__ == "__main__":
    main()

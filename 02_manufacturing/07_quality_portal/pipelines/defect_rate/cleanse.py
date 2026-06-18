"""不良率集計: データクレンジング"""
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    "日付": "date", "Date": "date",
    "ライン": "line", "ライン名": "line", "Line": "line",
    "製品名": "product", "品名": "product", "Product": "product",
    "検査数": "inspected", "検査件数": "inspected",
    "不良数": "defects", "不良件数": "defects",
}

files = sorted(Path(".").glob("*.csv"))
if not files:
    raise FileNotFoundError("CSVファイルが見つかりません")

dfs = []
for f in files:
    df = pd.read_csv(f, encoding="utf-8-sig")
    df = df.rename(columns={c: COLUMN_MAP[c] for c in df.columns if c in COLUMN_MAP})
    dfs.append(df)

df = pd.concat(dfs, ignore_index=True)

required = {"date", "line", "product", "inspected", "defects"}
missing = required - set(df.columns)
if missing:
    raise ValueError(f"必要な列が不足しています: {missing}\n必要列: 日付/ライン/製品名/検査数/不良数")

df["date"] = pd.to_datetime(df["date"])
df["inspected"] = pd.to_numeric(df["inspected"], errors="coerce").fillna(0).astype(int)
df["defects"] = pd.to_numeric(df["defects"], errors="coerce").fillna(0).astype(int)
df = df[df["inspected"] > 0]
df["defect_rate"] = df["defects"] / df["inspected"]

df.to_csv(OUTPUT_DIR / "cleaned_defect_rate.csv", index=False, encoding="utf-8-sig")
print(f"クレンジング完了: {len(df)}件")

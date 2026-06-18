"""歩留まりトレンド: データクレンジング"""
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    "日付": "date", "発生日": "date",
    "工程名": "process", "工程": "process", "Process": "process",
    "投入数": "input_qty", "投入量": "input_qty",
    "合格数": "passed", "合格量": "passed", "良品数": "passed",
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

required = {"date", "process", "input_qty", "passed"}
missing = required - set(df.columns)
if missing:
    raise ValueError(f"必要な列が不足しています: {missing}\n必要列: 日付/工程名/投入数/合格数")

df["date"] = pd.to_datetime(df["date"])
df["input_qty"] = pd.to_numeric(df["input_qty"], errors="coerce").fillna(0).astype(int)
df["passed"] = pd.to_numeric(df["passed"], errors="coerce").fillna(0).astype(int)
df = df[df["input_qty"] > 0]
df["yield_rate"] = df["passed"] / df["input_qty"]

df.to_csv(OUTPUT_DIR / "cleaned_yield.csv", index=False, encoding="utf-8-sig")
print(f"クレンジング完了: {len(df)}件")

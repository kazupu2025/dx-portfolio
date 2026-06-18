"""検査員別実績: データクレンジング"""
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    "日付": "date", "検査日": "date",
    "検査員名": "inspector", "検査員": "inspector",
    "シフト": "shift",
    "検査数": "inspected", "検査件数": "inspected",
    "合格数": "passed", "合格件数": "passed", "良品数": "passed",
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

required = {"date", "inspector", "inspected", "passed"}
missing = required - set(df.columns)
if missing:
    raise ValueError(f"必要な列が不足しています: {missing}\n必要列: 日付/検査員名/検査数/合格数")

df["date"] = pd.to_datetime(df["date"])
df["inspected"] = pd.to_numeric(df["inspected"], errors="coerce").fillna(0).astype(int)
df["passed"] = pd.to_numeric(df["passed"], errors="coerce").fillna(0).astype(int)
df = df[df["inspected"] > 0]
df["pass_rate"] = df["passed"] / df["inspected"]
if "shift" not in df.columns:
    df["shift"] = "未設定"

df.to_csv(OUTPUT_DIR / "cleaned_inspector.csv", index=False, encoding="utf-8-sig")
print(f"クレンジング完了: {len(df)}件")

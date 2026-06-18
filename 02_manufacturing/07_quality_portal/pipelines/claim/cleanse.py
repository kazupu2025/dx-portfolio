"""クレーム集計: データクレンジング"""
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    "日付": "date", "発生日": "date",
    "仕入先名": "supplier", "仕入先": "supplier", "取引先": "supplier",
    "不良カテゴリ": "category", "不良種別": "category", "カテゴリ": "category",
    "対応状況": "status", "ステータス": "status",
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

required = {"date", "supplier", "category", "status"}
missing = required - set(df.columns)
if missing:
    raise ValueError(f"必要な列が不足しています: {missing}\n必要列: 日付/仕入先名/不良カテゴリ/対応状況")

df["date"] = pd.to_datetime(df["date"])
valid_statuses = {"未対応", "対応中", "完了"}
df["status"] = df["status"].where(df["status"].isin(valid_statuses), "未対応")
df = df.dropna(subset=["supplier", "category"])

df.to_csv(OUTPUT_DIR / "cleaned_claim.csv", index=False, encoding="utf-8-sig")
print(f"クレンジング完了: {len(df)}件")

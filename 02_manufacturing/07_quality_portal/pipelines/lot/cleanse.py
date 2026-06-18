"""ロット別合否判定: データクレンジング"""
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    "ロットID": "lot_id", "ロット番号": "lot_id", "Lot": "lot_id",
    "製品名": "product", "品名": "product",
    "検査日": "date", "日付": "date",
    "検査項目": "item", "検査内容": "item",
    "判定": "result", "合否": "result", "結果": "result",
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

required = {"lot_id", "product", "date", "item", "result"}
missing = required - set(df.columns)
if missing:
    raise ValueError(f"必要な列が不足しています: {missing}\n必要列: ロットID/製品名/検査日/検査項目/判定")

df["date"] = pd.to_datetime(df["date"])
valid_results = {"合格", "不合格"}
df["result"] = df["result"].where(df["result"].isin(valid_results), "不合格")
df = df.dropna(subset=["lot_id", "product"])

# ロット合否: 1件でも不合格があればそのロットは不合格
lot_pass = df.groupby("lot_id")["result"].apply(
    lambda x: "合格" if (x == "不合格").sum() == 0 else "不合格"
)
df = df.merge(lot_pass.rename("lot_result"), on="lot_id", how="left")

df.to_csv(OUTPUT_DIR / "cleaned_lot.csv", index=False, encoding="utf-8-sig")
print(f"クレンジング完了: {len(df)}件")

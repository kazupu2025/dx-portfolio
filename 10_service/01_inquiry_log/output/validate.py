"""
B-15 バリデーション (18チェック)
"""
import sys
import yaml
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
OUT  = Path(__file__).resolve().parent
CFG_PATH  = BASE / "config.yml"
CSV_PATH  = OUT / "cleaned_inquiry_202401.csv"
LOG_PATH  = OUT / "cleanse.log"

with open(CFG_PATH, encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

VALID_CATEGORIES  = {"請求・支払い", "製品不具合", "使い方・操作方法", "配送・到着", "返品・交換", "その他"}
VALID_RESOLUTIONS = {"解決済", "対応中", "未解決", "エスカレ済"}
VALID_CHANNELS    = {"電話", "メール", "チャット", "SNS"}

results = []

def check(name: str, ok: bool, detail: str = ""):
    status = "PASS" if ok else "FAIL"
    msg = f"[{status}] {name}"
    if detail:
        msg += f" - {detail}"
    results.append((name, ok, detail))
    print(msg)
    return ok

# 1. csv_exists
if not check("csv_exists", CSV_PATH.exists(), str(CSV_PATH)):
    print("CSVが存在しません。クレンジングを先に実行してください。")
    sys.exit(1)

# 2. log_exists
check("log_exists", LOG_PATH.exists(), str(LOG_PATH))

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

REQUIRED_COLS = [
    "inquiry_id","received_at","completed_at",
    "operator_id","operator_name","channel",
    "inquiry_text","category","resolution",
    "escalation","response_minutes","is_resolved","is_escalated"
]

# 3. schema
missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
check("schema", len(missing_cols)==0, f"missing: {missing_cols}" if missing_cols else "all columns present")

# 4. inquiry_id_nan
check("inquiry_id_nan", df["inquiry_id"].isna().sum()==0, f"null count: {df['inquiry_id'].isna().sum()}")

# 5. received_at_nan
check("received_at_nan", df["received_at"].isna().sum()==0, f"null count: {df['received_at'].isna().sum()}")

# 6. operator_id_nan
check("operator_id_nan", df["operator_id"].isna().sum()==0, f"null count: {df['operator_id'].isna().sum()}")

# 7. category_nan
check("category_nan", df["category"].isna().sum()==0, f"null count: {df['category'].isna().sum()}")

# 8. resolution_nan
check("resolution_nan", df["resolution"].isna().sum()==0, f"null count: {df['resolution'].isna().sum()}")

# 9. response_minutes_nan
check("response_minutes_nan", df["response_minutes"].isna().sum()==0, f"null count: {df['response_minutes'].isna().sum()}")

# 10. received_at_format (YYYY-MM-DD HH:MM)
import re
fmt_ok = df["received_at"].dropna().apply(lambda x: bool(re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", str(x)))).all()
check("received_at_format", fmt_ok, "YYYY-MM-DD HH:MM format")

# 11. received_at_range (2024-01データ)
in_range = df["received_at"].dropna().apply(lambda x: str(x).startswith("2024-01")).all()
check("received_at_range", in_range, "all in 2024-01")

# 12. response_minutes_positive
pos_ok = (pd.to_numeric(df["response_minutes"], errors="coerce") > 0).all()
check("response_minutes_positive", bool(pos_ok), f"min={df['response_minutes'].min()}")

# 13. category_values
invalid_cats = set(df["category"].unique()) - VALID_CATEGORIES
check("category_values", len(invalid_cats)==0, f"invalid: {invalid_cats}" if invalid_cats else "all valid")

# 14. resolution_values
invalid_res = set(df["resolution"].unique()) - VALID_RESOLUTIONS
check("resolution_values", len(invalid_res)==0, f"invalid: {invalid_res}" if invalid_res else "all valid")

# 15. channel_values
invalid_ch = set(df["channel"].unique()) - VALID_CHANNELS
check("channel_values", len(invalid_ch)==0, f"invalid: {invalid_ch}" if invalid_ch else "all valid")

# 16. operator_count
op_count = df["operator_id"].nunique()
check("operator_count", op_count == cfg["expected_operator_count"], f"found: {op_count}, expected: {cfg['expected_operator_count']}")

# 17. category_count
cat_count = df["category"].nunique()
check("category_count", cat_count == cfg["expected_category_count"], f"found: {cat_count}, expected: {cfg['expected_category_count']}")

# 18. row_count
n = len(df)
check("row_count", cfg["min_rows"] <= n <= cfg["max_rows"], f"rows={n}, expected {cfg['min_rows']}~{cfg['max_rows']}")

# サマリー
passed = sum(1 for _, ok, _ in results if ok)
total  = len(results)
print(f"\n=== 検証結果: {passed}/{total} PASS ===")
if passed < total:
    sys.exit(1)

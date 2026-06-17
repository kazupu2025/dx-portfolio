# -*- coding: utf-8 -*-
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CSV_PATH = os.path.join(OUTPUT_DIR, "cleaned_visits_202401.csv")

results = []


def check(label, condition):
    status = "[PASS]" if condition else "[FAIL]"
    results.append((status, label))
    print("{} {}".format(status, label))


# 1. File exists
check("ファイルが存在する", os.path.exists(CSV_PATH))

if os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
else:
    df = pd.DataFrame()

# 2. Row count >= 420
check("行数が420件以上", len(df) >= 420)

# 3. Required columns exist
required_cols = [
    "visit_date", "visit_id", "property_type", "area", "staff_id",
    "asking_price", "visit_count_cumulative", "days_to_contract",
    "is_contracted", "price_tier", "conversion_speed", "source_file"
]
check("必須列が存在する", all(c in df.columns for c in required_cols))

# 4. visit_date format YYYY-MM-DD
if "visit_date" in df.columns:
    try:
        pd.to_datetime(df["visit_date"], format="%Y-%m-%d")
        check("visit_dateフォーマットがYYYY-MM-DD", True)
    except Exception:
        check("visit_dateフォーマットがYYYY-MM-DD", False)
else:
    check("visit_dateフォーマットがYYYY-MM-DD", False)

# 5. visit_id uniqueness
if "visit_id" in df.columns:
    check("visit_idが一意", df["visit_id"].nunique() == len(df))
else:
    check("visit_idが一意", False)

# 6. property_type 4 kinds
if "property_type" in df.columns:
    check("property_typeが4種類", df["property_type"].nunique() == 4)
else:
    check("property_typeが4種類", False)

# 7. area 4 kinds
if "area" in df.columns:
    check("areaが4種類", df["area"].nunique() == 4)
else:
    check("areaが4種類", False)

# 8. asking_price > 0
if "asking_price" in df.columns:
    check("asking_priceが全て正の値", (pd.to_numeric(df["asking_price"], errors="coerce") > 0).all())
else:
    check("asking_priceが全て正の値", False)

# 9. visit_count_cumulative >= 1
if "visit_count_cumulative" in df.columns:
    check("visit_count_cumulativeが全て1以上", (pd.to_numeric(df["visit_count_cumulative"], errors="coerce") >= 1).all())
else:
    check("visit_count_cumulativeが全て1以上", False)

# 10. is_contracted is 0 or 1 only
if "is_contracted" in df.columns:
    vals = pd.to_numeric(df["is_contracted"], errors="coerce").dropna().astype(int)
    check("is_contractedが0/1のみ", set(vals.unique()).issubset({0, 1}))
else:
    check("is_contractedが0/1のみ", False)

# 11. price_tier 3 kinds
if "price_tier" in df.columns:
    check("price_tierが3種類", df["price_tier"].nunique() == 3)
else:
    check("price_tierが3種類", False)

# 12. conversion_speed 3 kinds: "早期成約"/"通常成約"/"未成約"
if "conversion_speed" in df.columns:
    expected = {"早期成約", "通常成約", "未成約"}
    check("conversion_speedが3種類（早期成約/通常成約/未成約）", set(df["conversion_speed"].unique()) == expected)
else:
    check("conversion_speedが3種類（早期成約/通常成約/未成約）", False)

# 13. Missing rate <= 15% (excluding days_to_contract)
cols_for_missing = [c for c in required_cols if c != "days_to_contract"]
if all(c in df.columns for c in cols_for_missing) and len(df) > 0:
    miss_rates = df[cols_for_missing].isnull().mean()
    check("欠損率が15%以下（days_to_contract除く）", (miss_rates <= 0.15).all())
else:
    check("欠損率が15%以下（days_to_contract除く）", False)

# 14. source_file 3 kinds
if "source_file" in df.columns:
    check("source_fileが3種類", df["source_file"].nunique() == 3)
else:
    check("source_fileが3種類", False)

# 15. Contracted rows >= 1
if "is_contracted" in df.columns:
    check("成約件数が1件以上", (pd.to_numeric(df["is_contracted"], errors="coerce") == 1).sum() >= 1)
else:
    check("成約件数が1件以上", False)

# 16. Non-contracted rows >= 1
if "is_contracted" in df.columns:
    check("未成約件数が1件以上", (pd.to_numeric(df["is_contracted"], errors="coerce") == 0).sum() >= 1)
else:
    check("未成約件数が1件以上", False)

# 17. staff_id kinds >= 4
if "staff_id" in df.columns:
    check("staff_idの種類が4種類以上", df["staff_id"].nunique() >= 4)
else:
    check("staff_idの種類が4種類以上", False)

passed = sum(1 for s, _ in results if s == "[PASS]")
total = len(results)
print("")
print("Result: {}/{} checks passed".format(passed, total))

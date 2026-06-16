"""
C-23: validate.py -- クレンジング結果の品質チェック (18項目以上)
全PASS必須。絵文字・em-dashは使用しない(Windows CP932互換)。
"""

import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "output" / "cleaned_maintenance_202401.csv"

REQUIRED_COLS = [
    "property_id", "property_name", "area", "property_type",
    "cost_category", "occurrence_date", "cost_amount", "vendor_name",
    "is_urgent", "cost_per_unit_flag", "is_repair", "source_file",
]

EXPECTED_AREAS = {"渋谷区", "新宿区", "港区", "品川区", "目黒区"}
EXPECTED_PROPERTY_TYPES = {"マンション", "アパート", "テナントビル", "戸建て"}
EXPECTED_COST_CATEGORIES = {"管理費", "定期修繕", "緊急修繕", "清掃費", "設備点検"}
EXPECTED_FLAGS = {"高額", "中額", "少額"}

results = []


def check(label: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    msg = f"[{status}] {label}"
    if detail:
        msg += f" -- {detail}"
    print(msg)
    results.append(passed)


# -------------------------------------------------------------------
# 1. ファイル存在チェック
# -------------------------------------------------------------------
if not CSV_PATH.exists():
    print(f"[FAIL] CSV ファイルが存在しない: {CSV_PATH}")
    sys.exit(1)

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# -------------------------------------------------------------------
# 2. 行数チェック (400行以上)
# -------------------------------------------------------------------
check("行数 >= 400", len(df) >= 400, f"実際: {len(df)} 行")

# -------------------------------------------------------------------
# 3. 必須列の存在チェック
# -------------------------------------------------------------------
missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
check("必須列が全て存在する", len(missing_cols) == 0, f"不足: {missing_cols}")

# -------------------------------------------------------------------
# 4. occurrence_date の形式チェック (YYYY-MM-DD)
# -------------------------------------------------------------------
if "occurrence_date" in df.columns:
    invalid_dates = df["occurrence_date"].dropna().apply(
        lambda v: not str(v).strip()[:10].replace("-", "").isdigit()
    )
    check("occurrence_date が YYYY-MM-DD 形式", not invalid_dates.any(),
          f"不正件数: {invalid_dates.sum()}")
else:
    check("occurrence_date 列が存在する", False)

# -------------------------------------------------------------------
# 5. property_id の種類数 (30以上)
# -------------------------------------------------------------------
if "property_id" in df.columns:
    n_props = df["property_id"].nunique()
    check("property_id の種類数 >= 30", n_props >= 30, f"実際: {n_props}")
else:
    check("property_id 列が存在する", False)

# -------------------------------------------------------------------
# 6. area の種類数 (5種類)
# -------------------------------------------------------------------
if "area" in df.columns:
    areas = set(df["area"].dropna().unique())
    check("area の種類数 == 5", len(areas) == 5, f"実際: {areas}")
    check("area が期待エリアを含む",
          len(areas & EXPECTED_AREAS) == 5, f"期待: {EXPECTED_AREAS}, 実際: {areas}")
else:
    check("area 列が存在する", False)

# -------------------------------------------------------------------
# 7. property_type の種類数 (4種類)
# -------------------------------------------------------------------
if "property_type" in df.columns:
    prop_types = set(df["property_type"].dropna().unique())
    check("property_type に4種類含む",
          len(prop_types & EXPECTED_PROPERTY_TYPES) == 4,
          f"実際: {prop_types}")
else:
    check("property_type 列が存在する", False)

# -------------------------------------------------------------------
# 8. cost_category の種類数 (5種類)
# -------------------------------------------------------------------
if "cost_category" in df.columns:
    cats = set(df["cost_category"].dropna().unique())
    check("cost_category に5種類含む",
          len(cats & EXPECTED_COST_CATEGORIES) == 5,
          f"実際: {cats}")
else:
    check("cost_category 列が存在する", False)

# -------------------------------------------------------------------
# 9. cost_amount > 0
# -------------------------------------------------------------------
if "cost_amount" in df.columns:
    invalid_amount = (df["cost_amount"] <= 0).sum()
    check("cost_amount がすべて > 0", invalid_amount == 0, f"違反件数: {invalid_amount}")
else:
    check("cost_amount 列が存在する", False)

# -------------------------------------------------------------------
# 10. is_urgent が bool 型 (True/False)
# -------------------------------------------------------------------
if "is_urgent" in df.columns:
    unique_vals = set(df["is_urgent"].dropna().unique())
    is_bool = unique_vals.issubset({True, False})
    check("is_urgent が bool (True/False)", is_bool, f"実際の値: {unique_vals}")
else:
    check("is_urgent 列が存在する", False)

# -------------------------------------------------------------------
# 11. cost_per_unit_flag の値域チェック
# -------------------------------------------------------------------
if "cost_per_unit_flag" in df.columns:
    flag_vals = set(df["cost_per_unit_flag"].dropna().unique())
    check("cost_per_unit_flag が期待値域内",
          flag_vals.issubset(EXPECTED_FLAGS),
          f"実際の値: {flag_vals}")
else:
    check("cost_per_unit_flag 列が存在する", False)

# -------------------------------------------------------------------
# 12. cost_per_unit_flag の計算整合性
# -------------------------------------------------------------------
if "cost_per_unit_flag" in df.columns and "cost_amount" in df.columns:
    def expected_flag(x):
        if x > 500000:
            return "高額"
        elif x > 100000:
            return "中額"
        else:
            return "少額"
    expected = df["cost_amount"].apply(expected_flag)
    mismatch = (df["cost_per_unit_flag"] != expected).sum()
    check("cost_per_unit_flag の計算が正しい", mismatch == 0, f"不一致件数: {mismatch}")
else:
    check("cost_per_unit_flag 計算チェック用列が存在する", False)

# -------------------------------------------------------------------
# 13. is_repair の計算整合性
# -------------------------------------------------------------------
if "is_repair" in df.columns and "cost_category" in df.columns:
    expected_repair = df["cost_category"].isin(["定期修繕", "緊急修繕"])
    mismatch_repair = (df["is_repair"] != expected_repair).sum()
    check("is_repair の計算が正しい", mismatch_repair == 0, f"不一致件数: {mismatch_repair}")
else:
    check("is_repair 計算チェック用列が存在する", False)

# -------------------------------------------------------------------
# 14. source_file 列の存在と非空
# -------------------------------------------------------------------
if "source_file" in df.columns:
    empty_sf = df["source_file"].isna().sum()
    check("source_file が全行に存在する", empty_sf == 0, f"空件数: {empty_sf}")
else:
    check("source_file 列が存在する", False)

# -------------------------------------------------------------------
# 15. 欠損率 < 15% (主要列)
# -------------------------------------------------------------------
key_cols = [c for c in ["property_id", "area", "cost_category", "cost_amount", "occurrence_date"] if c in df.columns]
if key_cols:
    max_missing_rate = df[key_cols].isna().mean().max()
    check("主要列の欠損率 < 15%", max_missing_rate < 0.15,
          f"最大欠損率: {max_missing_rate:.2%}")
else:
    check("主要列の欠損率チェック", False)

# -------------------------------------------------------------------
# 16. source_file の種類数 (3ファイル)
# -------------------------------------------------------------------
if "source_file" in df.columns:
    n_files = df["source_file"].nunique()
    check("source_file の種類数 == 3 (3ファイル)", n_files == 3, f"実際: {n_files}")
else:
    check("source_file の種類数チェック", False)

# -------------------------------------------------------------------
# 17. vendor_name が非空
# -------------------------------------------------------------------
if "vendor_name" in df.columns:
    empty_vendor = df["vendor_name"].isna().sum()
    check("vendor_name に空欄がない", empty_vendor == 0, f"空件数: {empty_vendor}")
else:
    check("vendor_name 列が存在する", False)

# -------------------------------------------------------------------
# 18. property_name が非空
# -------------------------------------------------------------------
if "property_name" in df.columns:
    empty_name = df["property_name"].isna().sum()
    check("property_name に空欄がない", empty_name == 0, f"空件数: {empty_name}")
else:
    check("property_name 列が存在する", False)

# -------------------------------------------------------------------
# 19. is_repair が bool 型
# -------------------------------------------------------------------
if "is_repair" in df.columns:
    repair_vals = set(df["is_repair"].dropna().unique())
    is_repair_bool = repair_vals.issubset({True, False})
    check("is_repair が bool (True/False)", is_repair_bool, f"実際の値: {repair_vals}")
else:
    check("is_repair 列が存在する", False)

# -------------------------------------------------------------------
# 結果サマリー
# -------------------------------------------------------------------
total = len(results)
passed = sum(results)
failed = total - passed

print(f"\n結果: {passed}/{total} PASS")

if failed > 0:
    print(f"FAIL: {failed} 件の検証に失敗しました")
    sys.exit(1)
else:
    print("全チェック PASS")
    sys.exit(0)

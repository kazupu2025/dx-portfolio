"""
C-20: validate.py -- クレンジング結果の品質チェック (18項目以上)
全PASS必須。絵文字・em-dashは使用しない(Windows CP932互換)。
"""

import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "output" / "cleaned_labor_202401.csv"

REQUIRED_COLS = [
    "staff_id", "name", "store_id", "employment_type",
    "hourly_wage", "work_date", "clock_in", "clock_out",
    "break_minutes", "work_hours", "late_night",
    "base_wage", "late_night_premium", "total_wage", "overtime_hours",
    "source_file",
]

EXPECTED_STORES = {"R001_新宿店", "R002_渋谷店", "R003_池袋店"}
EXPECTED_EMP_TYPES = {"アルバイト", "パート", "社員"}

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
# 4. work_date の形式チェック (YYYY-MM-DD)
# -------------------------------------------------------------------
if "work_date" in df.columns:
    invalid_dates = df["work_date"].dropna().apply(
        lambda v: not str(v).strip()[:10].replace("-", "").isdigit()
    )
    check("work_date が YYYY-MM-DD 形式", not invalid_dates.any(),
          f"不正件数: {invalid_dates.sum()}")
else:
    check("work_date 列が存在する", False)

# -------------------------------------------------------------------
# 5. staff_id の種類数 (20以上)
# -------------------------------------------------------------------
if "staff_id" in df.columns:
    n_staff = df["staff_id"].nunique()
    check("staff_id の種類数 >= 20", n_staff >= 20, f"実際: {n_staff}")
else:
    check("staff_id 列が存在する", False)

# -------------------------------------------------------------------
# 6. store_id の種類数 (3店舗)
# -------------------------------------------------------------------
if "store_id" in df.columns:
    stores = set(df["store_id"].dropna().unique())
    check("store_id の種類数 == 3", len(stores) == 3, f"実際: {stores}")
    check("store_id が期待の店舗コードを含む",
          len(stores & EXPECTED_STORES) == 3, f"期待: {EXPECTED_STORES}, 実際: {stores}")
else:
    check("store_id 列が存在する", False)

# -------------------------------------------------------------------
# 7. employment_type の種類
# -------------------------------------------------------------------
if "employment_type" in df.columns:
    emp_types = set(df["employment_type"].dropna().unique())
    check("employment_type に3種類含む",
          len(emp_types & EXPECTED_EMP_TYPES) == 3,
          f"実際: {emp_types}")
else:
    check("employment_type 列が存在する", False)

# -------------------------------------------------------------------
# 8. hourly_wage > 0
# -------------------------------------------------------------------
if "hourly_wage" in df.columns:
    invalid_wage = (df["hourly_wage"] <= 0).sum()
    check("hourly_wage がすべて > 0", invalid_wage == 0, f"違反件数: {invalid_wage}")
else:
    check("hourly_wage 列が存在する", False)

# -------------------------------------------------------------------
# 9. work_hours >= 0
# -------------------------------------------------------------------
if "work_hours" in df.columns:
    invalid_wh = (df["work_hours"] < 0).sum()
    check("work_hours がすべて >= 0", invalid_wh == 0, f"違反件数: {invalid_wh}")
else:
    check("work_hours 列が存在する", False)

# -------------------------------------------------------------------
# 10. work_hours <= 12 (異常値チェック)
# -------------------------------------------------------------------
if "work_hours" in df.columns:
    over12 = (df["work_hours"] > 12).sum()
    check("work_hours <= 12 (異常値なし)", over12 == 0, f"超過件数: {over12}")

# -------------------------------------------------------------------
# 11. base_wage >= 0
# -------------------------------------------------------------------
if "base_wage" in df.columns:
    invalid_base = (df["base_wage"] < 0).sum()
    check("base_wage がすべて >= 0", invalid_base == 0, f"違反件数: {invalid_base}")
else:
    check("base_wage 列が存在する", False)

# -------------------------------------------------------------------
# 12. total_wage >= base_wage
# -------------------------------------------------------------------
if "total_wage" in df.columns and "base_wage" in df.columns:
    invalid_total = (df["total_wage"] < df["base_wage"]).sum()
    check("total_wage >= base_wage", invalid_total == 0, f"違反件数: {invalid_total}")
else:
    check("total_wage / base_wage 列が存在する", False)

# -------------------------------------------------------------------
# 13. late_night が bool 型 (True/False)
# -------------------------------------------------------------------
if "late_night" in df.columns:
    unique_vals = set(df["late_night"].dropna().unique())
    is_bool = unique_vals.issubset({True, False})
    check("late_night が bool (True/False)", is_bool, f"実際の値: {unique_vals}")
else:
    check("late_night 列が存在する", False)

# -------------------------------------------------------------------
# 14. late_night_premium の計算整合性
# -------------------------------------------------------------------
if all(c in df.columns for c in ("base_wage", "late_night", "late_night_premium")):
    expected_premium = (df["base_wage"] * 0.25 * df["late_night"].astype(int)).round(2)
    diff = (df["late_night_premium"] - expected_premium).abs()
    check("late_night_premium の計算が正しい (誤差 <= 1円)",
          (diff <= 1.0).all(), f"最大誤差: {diff.max():.2f}")
else:
    check("late_night_premium 計算チェック用列が存在する", False)

# -------------------------------------------------------------------
# 15. overtime_hours >= 0
# -------------------------------------------------------------------
if "overtime_hours" in df.columns:
    invalid_ot = (df["overtime_hours"] < 0).sum()
    check("overtime_hours >= 0", invalid_ot == 0, f"違反件数: {invalid_ot}")
else:
    check("overtime_hours 列が存在する", False)

# -------------------------------------------------------------------
# 16. source_file 列の存在と非空
# -------------------------------------------------------------------
if "source_file" in df.columns:
    empty_sf = df["source_file"].isna().sum()
    check("source_file が全行に存在する", empty_sf == 0, f"空件数: {empty_sf}")
else:
    check("source_file 列が存在する", False)

# -------------------------------------------------------------------
# 17. 欠損率 < 15% (主要列)
# -------------------------------------------------------------------
key_cols = [c for c in ["staff_id", "store_id", "work_date", "work_hours", "hourly_wage"] if c in df.columns]
if key_cols:
    max_missing_rate = df[key_cols].isna().mean().max()
    check("主要列の欠損率 < 15%", max_missing_rate < 0.15,
          f"最大欠損率: {max_missing_rate:.2%}")
else:
    check("主要列の欠損率チェック", False)

# -------------------------------------------------------------------
# 18. source_file の種類数 (3つのファイル)
# -------------------------------------------------------------------
if "source_file" in df.columns:
    n_files = df["source_file"].nunique()
    check("source_file の種類数 == 3 (3ファイル)", n_files == 3, f"実際: {n_files}")
else:
    check("source_file の種類数チェック", False)

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

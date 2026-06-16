"""
C-30: validate.py -- クレンジング結果の品質チェック (18項目以上)
全PASS必須。絵文字・em-dashは使用しない(Windows CP932互換)。
print文に絵文字(YEN記号・em-dash等)は使用しない。[PASS]/[FAIL]を使う。
"""

import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "output" / "cleaned_labor_cost_202401.csv"

REQUIRED_COLS = [
    "year_month", "department", "employment_type",
    "head_count", "budget_cost", "actual_cost", "overtime_cost",
    "variance_amount", "variance_rate", "cost_per_person", "variance_flag",
    "source_file",
]

EXPECTED_DEPARTMENTS = {"営業部", "製造部", "管理部", "開発部", "物流部"}
EXPECTED_EMP_TYPES = {"正社員", "契約社員", "パート"}
EXPECTED_FLAGS = {"超過", "節約", "正常"}

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
# 4. year_month フォーマット (YYYY-MM)
# -------------------------------------------------------------------
if "year_month" in df.columns:
    import re
    pattern = re.compile(r"^\d{4}-\d{2}$")
    invalid_ym = df["year_month"].dropna().apply(lambda v: not bool(pattern.match(str(v).strip())))
    check("year_month が YYYY-MM 形式", not invalid_ym.any(),
          f"不正件数: {invalid_ym.sum()}")
else:
    check("year_month 列が存在する", False)

# -------------------------------------------------------------------
# 5. department が5種類
# -------------------------------------------------------------------
if "department" in df.columns:
    depts = set(df["department"].dropna().unique())
    check("department が5種類", len(depts) == 5, f"実際: {depts}")
    check("department が期待の部門を含む",
          depts == EXPECTED_DEPARTMENTS,
          f"期待: {EXPECTED_DEPARTMENTS}, 実際: {depts}")
else:
    check("department 列が存在する", False)

# -------------------------------------------------------------------
# 6. employment_type が3種類
# -------------------------------------------------------------------
if "employment_type" in df.columns:
    emp_types = set(df["employment_type"].dropna().unique())
    check("employment_type が3種類",
          len(emp_types & EXPECTED_EMP_TYPES) == 3,
          f"実際: {emp_types}")
else:
    check("employment_type 列が存在する", False)

# -------------------------------------------------------------------
# 7. head_count > 0
# -------------------------------------------------------------------
if "head_count" in df.columns:
    invalid_hc = (df["head_count"] <= 0).sum()
    check("head_count がすべて > 0", invalid_hc == 0, f"違反件数: {invalid_hc}")
else:
    check("head_count 列が存在する", False)

# -------------------------------------------------------------------
# 8. budget_cost > 0
# -------------------------------------------------------------------
if "budget_cost" in df.columns:
    invalid_bc = (df["budget_cost"] <= 0).sum()
    check("budget_cost がすべて > 0", invalid_bc == 0, f"違反件数: {invalid_bc}")
else:
    check("budget_cost 列が存在する", False)

# -------------------------------------------------------------------
# 9. actual_cost > 0
# -------------------------------------------------------------------
if "actual_cost" in df.columns:
    invalid_ac = (df["actual_cost"] <= 0).sum()
    check("actual_cost がすべて > 0", invalid_ac == 0, f"違反件数: {invalid_ac}")
else:
    check("actual_cost 列が存在する", False)

# -------------------------------------------------------------------
# 10. overtime_cost >= 0
# -------------------------------------------------------------------
if "overtime_cost" in df.columns:
    invalid_ot = (df["overtime_cost"] < 0).sum()
    check("overtime_cost がすべて >= 0", invalid_ot == 0, f"違反件数: {invalid_ot}")
else:
    check("overtime_cost 列が存在する", False)

# -------------------------------------------------------------------
# 11. variance_amount の整合性 (actual_cost - budget_cost, 誤差1円以内)
# -------------------------------------------------------------------
if all(c in df.columns for c in ("actual_cost", "budget_cost", "variance_amount")):
    expected_va = df["actual_cost"] - df["budget_cost"]
    diff = (df["variance_amount"] - expected_va).abs()
    check("variance_amount の計算が正しい (誤差 <= 1円)",
          (diff <= 1.0).all(), f"最大誤差: {diff.max():.2f}")
else:
    check("variance_amount 計算チェック用列が存在する", False)

# -------------------------------------------------------------------
# 12. variance_flag が "超過"/"節約"/"正常" のみ
# -------------------------------------------------------------------
if "variance_flag" in df.columns:
    flag_vals = set(df["variance_flag"].dropna().unique())
    check("variance_flag が正規値のみ",
          flag_vals.issubset(EXPECTED_FLAGS),
          f"実際の値: {flag_vals}")
else:
    check("variance_flag 列が存在する", False)

# -------------------------------------------------------------------
# 13. cost_per_person が正 (または NaN)
# -------------------------------------------------------------------
if "cost_per_person" in df.columns:
    invalid_cpp = (df["cost_per_person"].dropna() <= 0).sum()
    check("cost_per_person が正 (またはNaN)", invalid_cpp == 0, f"違反件数: {invalid_cpp}")
else:
    check("cost_per_person 列が存在する", False)

# -------------------------------------------------------------------
# 14. 超過件数 >= 1
# -------------------------------------------------------------------
if "variance_flag" in df.columns:
    over_count = (df["variance_flag"] == "超過").sum()
    check("超過 フラグが1件以上存在する", over_count >= 1, f"超過件数: {over_count}")
else:
    check("variance_flag 列が存在する (超過件数チェック用)", False)

# -------------------------------------------------------------------
# 15. source_file 列の存在
# -------------------------------------------------------------------
if "source_file" in df.columns:
    empty_sf = df["source_file"].isna().sum()
    check("source_file が全行に存在する", empty_sf == 0, f"空件数: {empty_sf}")
else:
    check("source_file 列が存在する", False)

# -------------------------------------------------------------------
# 16. 欠損率 <= 15% (主要列)
# -------------------------------------------------------------------
key_cols = [c for c in ["year_month", "department", "employment_type",
                         "budget_cost", "actual_cost"] if c in df.columns]
if key_cols:
    max_missing_rate = df[key_cols].isna().mean().max()
    check("主要列の欠損率 <= 15%", max_missing_rate <= 0.15,
          f"最大欠損率: {max_missing_rate:.2%}")
else:
    check("主要列の欠損率チェック", False)

# -------------------------------------------------------------------
# 17. source_file の種類数 (3ファイル)
# -------------------------------------------------------------------
if "source_file" in df.columns:
    n_files = df["source_file"].nunique()
    check("source_file の種類数 == 3 (3ファイル)", n_files == 3, f"実際: {n_files}")
else:
    check("source_file の種類数チェック", False)

# -------------------------------------------------------------------
# 18. overtime_cost <= actual_cost (整合性チェック)
# -------------------------------------------------------------------
if all(c in df.columns for c in ("overtime_cost", "actual_cost")):
    invalid_ot_ratio = (df["overtime_cost"] > df["actual_cost"]).sum()
    check("overtime_cost <= actual_cost", invalid_ot_ratio == 0,
          f"違反件数: {invalid_ot_ratio}")
else:
    check("overtime_cost / actual_cost 列が存在する", False)

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

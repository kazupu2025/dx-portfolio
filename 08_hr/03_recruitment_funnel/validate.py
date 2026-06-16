"""
C-33: validate.py -- クレンジング結果の品質チェック (18項目以上)
全PASS必須。絵文字・em-dashは使用しない(Windows CP932互換)。
print文に絵文字(YEN記号・em-dash等)は使用しない。[PASS]/[FAIL]を使う。
"""

import re
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "output" / "cleaned_recruitment_202401.csv"

REQUIRED_COLS = [
    "apply_date", "applicant_id", "job_type", "channel",
    "reached_phase", "hire_result", "screening_days",
    "is_hired", "phase_order", "passed_first_screen",
    "source_file",
]

VALID_JOB_TYPES = {"エンジニア", "営業", "事務", "マーケティング", "製造"}
VALID_CHANNELS = {"転職サイト", "エージェント", "リファラル", "自社HP"}
VALID_PHASES = {"書類選考", "一次面接", "二次面接", "最終面接", "内定"}
VALID_HIRE_RESULTS = {"採用", "不採用"}

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
# 4. applicant_id のユニーク性
# -------------------------------------------------------------------
if "applicant_id" in df.columns:
    dup_count = df["applicant_id"].duplicated().sum()
    check("applicant_id にユニーク性がある", dup_count == 0, f"重複件数: {dup_count}")
else:
    check("applicant_id 列が存在する", False)

# -------------------------------------------------------------------
# 5. 日付フォーマット YYYY-MM-DD
# -------------------------------------------------------------------
if "apply_date" in df.columns:
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    invalid_dates = df["apply_date"].dropna().apply(
        lambda v: not bool(pattern.match(str(v).strip()))
    )
    check("apply_date が YYYY-MM-DD 形式", not invalid_dates.any(),
          f"不正件数: {invalid_dates.sum()}")
else:
    check("apply_date 列が存在する", False)

# -------------------------------------------------------------------
# 6. job_type が5種類
# -------------------------------------------------------------------
if "job_type" in df.columns:
    actual_jobs = set(df["job_type"].dropna().unique())
    check("job_type が5種類", len(actual_jobs) == 5, f"実際: {actual_jobs}")
    check("job_type が期待の職種を含む",
          actual_jobs == VALID_JOB_TYPES,
          f"期待: {VALID_JOB_TYPES}, 実際: {actual_jobs}")
else:
    check("job_type 列が存在する", False)

# -------------------------------------------------------------------
# 7. channel が4種類
# -------------------------------------------------------------------
if "channel" in df.columns:
    actual_channels = set(df["channel"].dropna().unique())
    check("channel が4種類", len(actual_channels) == 4, f"実際: {actual_channels}")
    check("channel が期待の値を含む",
          actual_channels == VALID_CHANNELS,
          f"期待: {VALID_CHANNELS}, 実際: {actual_channels}")
else:
    check("channel 列が存在する", False)

# -------------------------------------------------------------------
# 8. reached_phase が5種類以内（有効値のみ）
# -------------------------------------------------------------------
if "reached_phase" in df.columns:
    actual_phases = set(df["reached_phase"].dropna().unique())
    invalid_phases = actual_phases - VALID_PHASES
    check("reached_phase が有効値のみ",
          len(invalid_phases) == 0,
          f"無効値: {invalid_phases}")
    check("reached_phase が5種類以内", len(actual_phases) <= 5, f"実際: {actual_phases}")
else:
    check("reached_phase 列が存在する", False)

# -------------------------------------------------------------------
# 9. hire_result が "採用"/"不採用" のみ
# -------------------------------------------------------------------
if "hire_result" in df.columns:
    actual_results = set(df["hire_result"].dropna().unique())
    invalid_results = actual_results - VALID_HIRE_RESULTS
    check("hire_result が 採用/不採用 のみ",
          len(invalid_results) == 0,
          f"無効値: {invalid_results}")
else:
    check("hire_result 列が存在する", False)

# -------------------------------------------------------------------
# 10. screening_days > 0
# -------------------------------------------------------------------
if "screening_days" in df.columns:
    invalid_days = (df["screening_days"] <= 0).sum()
    check("screening_days がすべて > 0", invalid_days == 0, f"違反件数: {invalid_days}")
else:
    check("screening_days 列が存在する", False)

# -------------------------------------------------------------------
# 11. is_hired が 0 または 1 のみ
# -------------------------------------------------------------------
if "is_hired" in df.columns:
    invalid_hired = (~df["is_hired"].isin([0, 1])).sum()
    check("is_hired が 0 または 1 のみ", invalid_hired == 0, f"違反件数: {invalid_hired}")
else:
    check("is_hired 列が存在する", False)

# -------------------------------------------------------------------
# 12. phase_order が 1〜5 の範囲
# -------------------------------------------------------------------
if "phase_order" in df.columns:
    invalid_order = (~df["phase_order"].isin([1, 2, 3, 4, 5])).sum()
    check("phase_order が 1〜5 の範囲", invalid_order == 0, f"違反件数: {invalid_order}")
else:
    check("phase_order 列が存在する", False)

# -------------------------------------------------------------------
# 13. 採用件数 >= 1
# -------------------------------------------------------------------
if "is_hired" in df.columns:
    hired_count = (df["is_hired"] == 1).sum()
    check("採用件数 >= 1", hired_count >= 1, f"採用件数: {hired_count}")
else:
    check("is_hired 列が存在する (採用件数チェック用)", False)

# -------------------------------------------------------------------
# 14. 書類選考通過件数 >= 1
# -------------------------------------------------------------------
if "passed_first_screen" in df.columns:
    passed_first = (df["passed_first_screen"] == 1).sum()
    check("書類選考通過件数 >= 1", passed_first >= 1, f"通過件数: {passed_first}")
else:
    check("passed_first_screen 列が存在する", False)

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
key_cols = [c for c in ["apply_date", "job_type", "channel", "reached_phase", "hire_result"]
            if c in df.columns]
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
# 18. 内定到達者の採用結果は全員"採用"
# -------------------------------------------------------------------
if all(c in df.columns for c in ("reached_phase", "hire_result")):
    naitei_rows = df[df["reached_phase"] == "内定"]
    if len(naitei_rows) > 0:
        not_hired = (naitei_rows["hire_result"] != "採用").sum()
        check("内定到達者の採用結果は全員「採用」", not_hired == 0,
              f"違反件数: {not_hired}")
    else:
        check("内定到達者チェック (内定者 0 件のためスキップ)", True)
else:
    check("reached_phase/hire_result 列が存在する (内定チェック用)", False)

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

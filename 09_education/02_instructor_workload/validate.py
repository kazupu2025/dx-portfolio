import json
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
CSV_PATH = OUTPUT_DIR / "cleaned_instructor_202401.csv"

results = []


def check(check_id, name, category, condition, detail="", fix_hint=""):
    status = "PASS" if condition else "FAIL"
    results.append({
        "id": check_id, "name": name, "category": category,
        "status": status,
        "detail": "" if condition else detail,
        "fix_hint": "" if condition else fix_hint,
    })
    return condition


# 1: CSV存在確認
check(1, "csv_exists", "存在", CSV_PATH.exists(),
      f"{CSV_PATH} が存在しない", "cleanse.py を再実行")

if not CSV_PATH.exists():
    out = {"passed": 0, "failed": len(results), "all_passed": False, "results": results}
    (OUTPUT_DIR / "result.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    raise SystemExit(1)

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

ALL_COLS = [
    "instructor_id", "name", "specialty", "employment_type",
    "session_date", "course_name", "lesson_count", "attendee_count",
    "venue", "hourly_rate", "source_file",
    "lesson_hours", "lesson_cost", "cost_per_attendee", "workload_flag",
]
missing_cols = [c for c in ALL_COLS if c not in df.columns]

# 2: 行数400以上
check(2, "row_count_min", "網羅性", len(df) >= 400,
      f"行数: {len(df)} (期待: 400以上)", "サンプルデータ再生成またはcleanse.py確認")

# 3: 必須列すべて存在
check(3, "required_columns", "スキーマ", len(missing_cols) == 0,
      f"欠落列: {missing_cols}", "COLUMN_MAP と cleanse.py を確認")

# 4: session_date の NULL なし
nan_date = df["session_date"].isna().sum() if "session_date" in df.columns else len(df)
check(4, "session_date_no_null", "完全性", nan_date == 0,
      f"session_date NaN: {nan_date}", "normalize_date() を確認")

# 5: session_date 形式 YYYY-MM-DD
if "session_date" in df.columns:
    bad_dates = df["session_date"].dropna()[
        ~df["session_date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")
    ]
    check(5, "session_date_format", "値域", len(bad_dates) == 0,
          f"不正日付: {len(bad_dates)}", "normalize_date() を確認")
else:
    check(5, "session_date_format", "値域", False, "session_date列なし", "cleanse.py を確認")

# 6: instructor_id NULL なし
nan_id = df["instructor_id"].isna().sum() if "instructor_id" in df.columns else len(df)
check(6, "instructor_id_no_null", "完全性", nan_id == 0,
      f"instructor_id NaN: {nan_id}", "COLUMN_MAP を確認")

# 7: instructor_id の種類 15以上
n_instructors = df["instructor_id"].nunique() if "instructor_id" in df.columns else 0
check(7, "instructor_id_variety", "網羅性", n_instructors >= 15,
      f"講師ID種類: {n_instructors} (期待: 15以上)", "_gen_sample_data.py を確認")

# 8: specialty の種類 5
n_specialty = df["specialty"].nunique() if "specialty" in df.columns else 0
check(8, "specialty_variety", "網羅性", n_specialty >= 5,
      f"specialty種類: {n_specialty} (期待: 5)", "_gen_sample_data.py を確認")

# 9: employment_type の種類 3
n_emp = df["employment_type"].nunique() if "employment_type" in df.columns else 0
check(9, "employment_type_variety", "網羅性", n_emp == 3,
      f"employment_type種類: {n_emp} (期待: 3)", "_gen_sample_data.py を確認")

# 10: lesson_count > 0
if "lesson_count" in df.columns:
    n_le0 = (df["lesson_count"] <= 0).sum()
    check(10, "lesson_count_positive", "値域", n_le0 == 0,
          f"lesson_count<=0: {n_le0}", "clip(lower=0) と生成ロジックを確認")
else:
    check(10, "lesson_count_positive", "値域", False, "lesson_count列なし", "cleanse.py を確認")

# 11: lesson_count <= 4 (1日最大4コマ)
if "lesson_count" in df.columns:
    n_gt4 = (df["lesson_count"] > 4).sum()
    check(11, "lesson_count_max4", "値域", n_gt4 == 0,
          f"lesson_count>4: {n_gt4}", "サンプルデータ生成ロジックを確認")
else:
    check(11, "lesson_count_max4", "値域", False, "lesson_count列なし", "cleanse.py を確認")

# 12: hourly_rate > 0
if "hourly_rate" in df.columns:
    n_hr0 = (df["hourly_rate"] <= 0).sum()
    check(12, "hourly_rate_positive", "値域", n_hr0 == 0,
          f"hourly_rate<=0: {n_hr0}", "normalize_numeric() を確認")
else:
    check(12, "hourly_rate_positive", "値域", False, "hourly_rate列なし", "cleanse.py を確認")

# 13: attendee_count > 0
if "attendee_count" in df.columns:
    n_ac0 = (df["attendee_count"] <= 0).sum()
    check(13, "attendee_count_positive", "値域", n_ac0 == 0,
          f"attendee_count<=0: {n_ac0}", "サンプルデータ生成ロジックを確認")
else:
    check(13, "attendee_count_positive", "値域", False, "attendee_count列なし", "cleanse.py を確認")

# 14: lesson_cost > 0
if "lesson_cost" in df.columns:
    n_lc0 = (df["lesson_cost"] <= 0).sum()
    check(14, "lesson_cost_positive", "値域", n_lc0 == 0,
          f"lesson_cost<=0: {n_lc0}", "lesson_cost計算を確認")
else:
    check(14, "lesson_cost_positive", "値域", False, "lesson_cost列なし", "cleanse.py を確認")

# 15: workload_flag の値域
if "workload_flag" in df.columns:
    valid_flags = {"高負荷", "通常"}
    bad_flags = ~df["workload_flag"].isin(valid_flags)
    check(15, "workload_flag_values", "値域", bad_flags.sum() == 0,
          f"不正な workload_flag: {df[bad_flags]['workload_flag'].unique().tolist()}", "cleanse.py を確認")
else:
    check(15, "workload_flag_values", "値域", False, "workload_flag列なし", "cleanse.py を確認")

# 16: source_file 列が存在し NULL なし
if "source_file" in df.columns:
    nan_sf = df["source_file"].isna().sum()
    check(16, "source_file_no_null", "完全性", nan_sf == 0,
          f"source_file NaN: {nan_sf}", "cleanse.py の source_file 設定を確認")
else:
    check(16, "source_file_no_null", "完全性", False, "source_file列なし", "cleanse.py を確認")

# 17: lesson_hours の計算正確性 (lesson_hours == lesson_count * 1.5)
if "lesson_hours" in df.columns and "lesson_count" in df.columns:
    diff = (df["lesson_hours"] - df["lesson_count"] * 1.5).abs()
    check(17, "lesson_hours_calculation", "計算整合性", (diff < 0.01).all(),
          f"lesson_hours計算ずれ: {(diff >= 0.01).sum()}行", "lesson_hours = lesson_count * 1.5 を確認")
else:
    check(17, "lesson_hours_calculation", "計算整合性", False, "lesson_hours/lesson_count列なし", "cleanse.py を確認")

# 18: 全列の欠損率 15%以下 (cost_per_attendee は attendee=0 の場合NaN許容)
SKIP_NULL_CHECK = {"cost_per_attendee"}
if len(df) > 0:
    for col in [c for c in ALL_COLS if c in df.columns and c not in SKIP_NULL_CHECK]:
        null_rate = df[col].isna().mean()
        if null_rate > 0.15:
            check(18, f"null_rate_{col}", "品質", False,
                  f"{col} 欠損率: {null_rate:.1%}", "cleanse.py の欠損補完を確認")
            break
    else:
        check(18, "null_rate_all_cols", "品質", True)
else:
    check(18, "null_rate_all_cols", "品質", False, "データなし", "cleanse.py を確認")

passed = sum(1 for r in results if r["status"] == "PASS")
failed = len(results) - passed
output = {"passed": passed, "failed": failed, "all_passed": failed == 0, "results": results}
(OUTPUT_DIR / "result.json").write_text(
    json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
)

print(f"\n{'='*56}\n  チェック結果: {passed}/{len(results)} PASS\n{'='*56}")
for r in results:
    icon = "PASS" if r["status"] == "PASS" else "FAIL"
    line = f"  [{icon}]  [{r['category']:6s}] #{r['id']:02d} {r['name']}"
    if r["detail"]:
        line += f"\n         -> {r['detail']}\n         HINT: {r['fix_hint']}"
    print(line)
print(f"\n  全{len(results)}項目クリア!" if failed == 0 else f"\n  {failed}項目が失敗")
if failed > 0:
    raise SystemExit(1)

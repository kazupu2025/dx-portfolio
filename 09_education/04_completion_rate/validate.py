import json
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
CSV_PATH = OUTPUT_DIR / "cleaned_enrollment_202401.csv"

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


# 1: CSVファイル存在確認
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
    "enroll_date", "enroll_no", "course_name", "learner_type",
    "study_hours", "test_score", "status", "satisfaction",
    "source_file", "is_completed", "score_grade", "dropout_risk",
]
missing_cols = [c for c in ALL_COLS if c not in df.columns]

# 2: 行数 >= 420
check(2, "row_count_min", "網羅性", len(df) >= 420,
      f"行数: {len(df)} (期待: 420以上)", "サンプルデータ再生成またはcleanse.py確認")

# 3: 必須列の存在
check(3, "required_columns", "スキーマ", len(missing_cols) == 0,
      f"欠落列: {missing_cols}", "COLUMN_MAP と cleanse.py を確認")

# 4: enroll_noのユニーク性
if "enroll_no" in df.columns:
    dup_count = df["enroll_no"].duplicated().sum()
    check(4, "enroll_no_unique", "一意性", dup_count == 0,
          f"重複enroll_no: {dup_count}", "cleanse.py の drop_duplicates を確認")
else:
    check(4, "enroll_no_unique", "一意性", False, "enroll_no列なし", "cleanse.py を確認")

# 5: 日付フォーマット YYYY-MM-DD
if "enroll_date" in df.columns:
    bad_dates = df["enroll_date"].dropna()[
        ~df["enroll_date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")
    ]
    check(5, "enroll_date_format", "値域", len(bad_dates) == 0,
          f"不正日付: {len(bad_dates)}", "normalize_date() を確認")
else:
    check(5, "enroll_date_format", "値域", False, "enroll_date列なし", "cleanse.py を確認")

# 6: course_nameが5種類
if "course_name" in df.columns:
    n_courses = df["course_name"].nunique()
    check(6, "course_name_variety", "網羅性", n_courses == 5,
          f"course_name種類: {n_courses} (期待: 5)", "_gen_sample_data.py を確認")
else:
    check(6, "course_name_variety", "網羅性", False, "course_name列なし", "cleanse.py を確認")

# 7: learner_typeが3種類
if "learner_type" in df.columns:
    n_lt = df["learner_type"].nunique()
    check(7, "learner_type_variety", "網羅性", n_lt == 3,
          f"learner_type種類: {n_lt} (期待: 3)", "_gen_sample_data.py を確認")
else:
    check(7, "learner_type_variety", "網羅性", False, "learner_type列なし", "cleanse.py を確認")

# 8: study_hours > 0
if "study_hours" in df.columns:
    n_le0 = (df["study_hours"] <= 0).sum()
    check(8, "study_hours_positive", "値域", n_le0 == 0,
          f"study_hours<=0: {n_le0}", "サンプルデータ生成ロジックを確認")
else:
    check(8, "study_hours_positive", "値域", False, "study_hours列なし", "cleanse.py を確認")

# 9: test_scoreが0〜100の範囲
if "test_score" in df.columns:
    n_out = ((df["test_score"] < 0) | (df["test_score"] > 100)).sum()
    check(9, "test_score_range", "値域", n_out == 0,
          f"test_score範囲外: {n_out}", "サンプルデータ生成ロジックを確認")
else:
    check(9, "test_score_range", "値域", False, "test_score列なし", "cleanse.py を確認")

# 10: satisfactionが1〜5の範囲
if "satisfaction" in df.columns:
    n_out = ((df["satisfaction"] < 1) | (df["satisfaction"] > 5)).sum()
    check(10, "satisfaction_range", "値域", n_out == 0,
          f"satisfaction範囲外: {n_out}", "サンプルデータ生成ロジックを確認")
else:
    check(10, "satisfaction_range", "値域", False, "satisfaction列なし", "cleanse.py を確認")

# 11: statusが"修了"/"受講中"/"中途離脱"のみ
if "status" in df.columns:
    valid_statuses = {"修了", "受講中", "中途離脱"}
    bad_status = ~df["status"].isin(valid_statuses)
    check(11, "status_values", "値域", bad_status.sum() == 0,
          f"不正なstatus: {df[bad_status]['status'].unique().tolist()}", "cleanse.py を確認")
else:
    check(11, "status_values", "値域", False, "status列なし", "cleanse.py を確認")

# 12: is_completedが0または1のみ
if "is_completed" in df.columns:
    valid_ic = {0, 1}
    bad_ic = ~df["is_completed"].isin(valid_ic)
    check(12, "is_completed_values", "値域", bad_ic.sum() == 0,
          f"不正なis_completed: {df[bad_ic]['is_completed'].unique().tolist()}", "cleanse.py を確認")
else:
    check(12, "is_completed_values", "値域", False, "is_completed列なし", "cleanse.py を確認")

# 13: score_gradeが"優秀"/"合格"/"不合格"のみ
if "score_grade" in df.columns:
    valid_sg = {"優秀", "合格", "不合格"}
    bad_sg = ~df["score_grade"].isin(valid_sg)
    check(13, "score_grade_values", "値域", bad_sg.sum() == 0,
          f"不正なscore_grade: {df[bad_sg]['score_grade'].unique().tolist()}", "cleanse.py を確認")
else:
    check(13, "score_grade_values", "値域", False, "score_grade列なし", "cleanse.py を確認")

# 14: dropout_riskが"高"/"低"のみ
if "dropout_risk" in df.columns:
    valid_dr = {"高", "低"}
    bad_dr = ~df["dropout_risk"].isin(valid_dr)
    check(14, "dropout_risk_values", "値域", bad_dr.sum() == 0,
          f"不正なdropout_risk: {df[bad_dr]['dropout_risk'].unique().tolist()}", "cleanse.py を確認")
else:
    check(14, "dropout_risk_values", "値域", False, "dropout_risk列なし", "cleanse.py を確認")

# 15: source_file列の存在
check(15, "source_file_exists", "スキーマ", "source_file" in df.columns,
      "source_file列なし", "cleanse.py を確認")

# 16: 欠損率 <= 15%
SKIP_NULL_CHECK: set = set()
if len(df) > 0:
    fail_found = False
    for col in [c for c in ALL_COLS if c in df.columns and c not in SKIP_NULL_CHECK]:
        null_rate = df[col].isna().mean()
        if null_rate > 0.15:
            check(16, f"null_rate_{col}", "品質", False,
                  f"{col} 欠損率: {null_rate:.1%}", "cleanse.py の欠損補完を確認")
            fail_found = True
            break
    if not fail_found:
        check(16, "null_rate_all_cols", "品質", True)
else:
    check(16, "null_rate_all_cols", "品質", False, "データなし", "cleanse.py を確認")

# 17: source_fileが3種類
if "source_file" in df.columns:
    n_src = df["source_file"].nunique()
    check(17, "source_file_variety", "網羅性", n_src == 3,
          f"source_file種類: {n_src} (期待: 3)", "_gen_sample_data.py または cleanse.py を確認")
else:
    check(17, "source_file_variety", "網羅性", False, "source_file列なし", "cleanse.py を確認")

# 18: 修了件数 >= 1（is_completed=1）
if "is_completed" in df.columns:
    completed_count = (df["is_completed"] == 1).sum()
    check(18, "completed_count_positive", "網羅性", completed_count >= 1,
          f"is_completed=1の件数: {completed_count}", "サンプルデータ生成ロジックを確認")
else:
    check(18, "completed_count_positive", "網羅性", False, "is_completed列なし", "cleanse.py を確認")

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

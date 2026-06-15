"""
validate.py — クレンジング出力の18チェック（PDCAループ最大5ラウンド）
実行: cd 09_education/01_dropout_risk && python output/validate.py
"""
import sys, subprocess, time
from pathlib import Path
import pandas as pd
import yaml

BASE = Path(__file__).resolve().parent.parent
OUT  = BASE / "output"

def load_config() -> dict:
    with open(BASE / "config.yml", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_checks(df: pd.DataFrame, config: dict) -> list[tuple[str, bool, str]]:
    results = []

    def chk(name, ok, msg=""):
        results.append((name, ok, msg))

    csv_path = OUT / "cleaned_dropout_202401.csv"
    log_path = OUT / "cleanse.log"

    # 1. csv_exists
    chk("csv_exists", csv_path.exists(), str(csv_path))
    # 2. log_exists
    chk("log_exists", log_path.exists(), str(log_path))

    if df is None:
        for name in ["schema","student_id_nan","subject_nan","attendance_rate_nan",
                     "midterm_score_nan","final_score_nan","dropout_risk_score_nan",
                     "attendance_range","midterm_range","final_range","dropout_score_range",
                     "risk_category_values","subject_count","student_count","course_values","row_count"]:
            chk(name, False, "CSV読み込み失敗")
        return results

    required_cols = {"student_id","subject","attendance_rate","midterm_score","final_score",
                     "assignment_rate","engagement_score","dropout_risk_score","risk_category"}

    # 3. schema
    missing = required_cols - set(df.columns)
    chk("schema", len(missing)==0, f"欠損列: {missing}")
    # 4. student_id_nan
    chk("student_id_nan", df["student_id"].isna().sum()==0, f"NaN count: {df['student_id'].isna().sum()}")
    # 5. subject_nan
    chk("subject_nan", df["subject"].isna().sum()==0)
    # 6. attendance_rate_nan
    chk("attendance_rate_nan", df["attendance_rate"].isna().sum()==0)
    # 7. midterm_score_nan
    chk("midterm_score_nan", df["midterm_score"].isna().sum()==0)
    # 8. final_score_nan
    chk("final_score_nan", df["final_score"].isna().sum()==0)
    # 9. dropout_risk_score_nan
    chk("dropout_risk_score_nan", df["dropout_risk_score"].isna().sum()==0)
    # 10. attendance_range
    ok = (df["attendance_rate"].between(0, 100)).all()
    chk("attendance_range", ok, f"out of range: {(~df['attendance_rate'].between(0,100)).sum()}")
    # 11. midterm_range
    ok = (df["midterm_score"].between(0, 100)).all()
    chk("midterm_range", ok)
    # 12. final_range
    ok = (df["final_score"].between(0, 100)).all()
    chk("final_range", ok)
    # 13. dropout_score_range
    ok = (df["dropout_risk_score"].between(0, 100)).all()
    chk("dropout_score_range", ok, f"range: [{df['dropout_risk_score'].min()}, {df['dropout_risk_score'].max()}]")
    # 14. risk_category_values
    valid_cats = {"高リスク", "中リスク", "低リスク"}
    actual_cats = set(df["risk_category"].unique())
    chk("risk_category_values", actual_cats.issubset(valid_cats), f"unexpected: {actual_cats - valid_cats}")
    # 15. subject_count
    n_subj = df["subject"].nunique()
    chk("subject_count", n_subj == config["expected_subject_count"], f"got {n_subj}")
    # 16. student_count
    n_stu = df["student_id"].nunique()
    chk("student_count", n_stu == config["expected_student_count"], f"got {n_stu}")
    # 17. course_values
    n_course = df["course"].nunique() if "course" in df.columns else 0
    chk("course_values", n_course == config["expected_course_count"], f"got {n_course}")
    # 18. row_count
    n = len(df)
    chk("row_count", config["min_rows"] <= n <= config["max_rows"], f"got {n}")

    return results

def main():
    config = load_config()
    MAX_ROUNDS = 5

    for round_num in range(1, MAX_ROUNDS + 1):
        print(f"\n=== PDCA Round {round_num}/{MAX_ROUNDS} ===")

        # クレンジング実行
        result = subprocess.run(
            ["C:/Users/realp/miniconda3/python.exe", "output/cleanse.py"],
            cwd=str(BASE), capture_output=True, text=True, encoding="utf-8"
        )
        if result.returncode != 0:
            print("cleanse.py エラー:", result.stderr[-2000:])

        # CSV読み込み
        csv_path = OUT / "cleaned_dropout_202401.csv"
        try:
            df = pd.read_csv(csv_path, encoding="utf-8-sig") if csv_path.exists() else None
        except Exception as e:
            df = None
            print(f"CSV読み込みエラー: {e}")

        checks = run_checks(df, config)

        passed = sum(1 for _, ok, _ in checks if ok)
        total  = len(checks)
        print(f"結果: {passed}/{total} PASS")

        for name, ok, msg in checks:
            status = "PASS" if ok else "FAIL"
            print(f"  [{status}] {name}" + (f" - {msg}" if msg else ""))

        if passed == total:
            print(f"\n全{total}チェック PASS - 完了")
            sys.exit(0)

        if round_num < MAX_ROUNDS:
            print(f"FAILあり。Round {round_num+1} へ...")
            time.sleep(1)

    print(f"\n最大ラウンド到達。{passed}/{total} PASS")
    sys.exit(1 if passed < total else 0)

if __name__ == "__main__":
    main()

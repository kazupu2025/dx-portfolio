"""
cleanse.py — 受講生退学リスクデータのクレンジング
実行: cd 09_education/01_dropout_risk && python output/cleanse.py
"""
import sys, logging
from pathlib import Path
import pandas as pd
import numpy as np
import yaml

BASE = Path(__file__).resolve().parent.parent
OUT  = BASE / "output"
LOG  = OUT / "cleanse.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG, encoding="utf-8"), logging.StreamHandler()],
)
log = logging.getLogger(__name__)

COLUMN_MAP = {
    "受講生ID":    "student_id",   "StudentID":   "student_id",   "学生番号": "student_id",
    "氏名":        "student_name", "StudentName": "student_name", "名前": "student_name",
    "科目名":      "subject",      "Subject":     "subject",      "科目": "subject",
    "出席率(%)":   "attendance_rate","AttendanceRate":"attendance_rate","出席率": "attendance_rate",
    "中間テスト点数":"midterm_score","MidtermScore":"midterm_score","中間点": "midterm_score",
    "期末テスト点数":"final_score",  "FinalScore":  "final_score",  "期末点": "final_score",
    "課題提出率(%)":"assignment_rate","AssignmentRate":"assignment_rate","提出率": "assignment_rate",
    "参加スコア(1-5)":"engagement_score","EngagementScore":"engagement_score","積極性": "engagement_score",
    "入学月":      "enrollment_month","EnrollmentMonth":"enrollment_month",
    "コース":      "course",        "Course":      "course",       "コース名": "course",
}

KEEP_COLS = {
    "student_id", "student_name", "subject", "course", "enrollment_month",
    "attendance_rate", "midterm_score", "final_score", "assignment_rate", "engagement_score",
    "dropout_risk_score", "risk_category",
    "score_imputed", "source_file",
}

def load_config() -> dict:
    cfg_path = BASE / "config.yml"
    with open(cfg_path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def calc_risk_score(row, config: dict) -> float:
    att  = min(100, max(0, float(row.get("attendance_rate", 50) or 50)))
    mid  = min(100, max(0, float(row.get("midterm_score",  50) or 50)))
    fin  = min(100, max(0, float(row.get("final_score",    50) or 50)))
    asgn = min(100, max(0, float(row.get("assignment_rate", 50) or 50)))
    eng  = min(100, max(0, (float(row.get("engagement_score", 3) or 3) - 1) / 4 * 100))

    score = (
        att  * config["attendance_weight"]  +
        mid  * config["midterm_weight"]     +
        fin  * config["final_weight"]       +
        asgn * config["assignment_weight"]  +
        eng  * config["engagement_weight"]
    )
    return round(score, 1)

def classify_risk(score: float, config: dict) -> str:
    if score < config["high_risk_threshold"]:
        return "高リスク"
    elif score < config["medium_risk_threshold"]:
        return "中リスク"
    else:
        return "低リスク"

def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    df = df.rename(columns=COLUMN_MAP)
    df["source_file"] = path.name
    return df

def main():
    config = load_config()
    log.info("=== cleanse.py 開始 ===")

    csv_files = sorted(BASE.glob("*.csv"))
    if not csv_files:
        log.error("CSVファイルが見つかりません")
        sys.exit(1)

    frames = []
    for f in csv_files:
        log.info(f"読み込み: {f.name}")
        df = load_csv(f)
        frames.append(df)

    df = pd.concat(frames, ignore_index=True)
    log.info(f"統合行数: {len(df)}")

    # 数値列の欠損補完
    num_cols = ["attendance_rate", "midterm_score", "final_score", "assignment_rate", "engagement_score"]
    df["score_imputed"] = False
    for col in num_cols:
        if col in df.columns:
            mask = df[col].isna()
            if mask.any():
                log.warning(f"{col}: {mask.sum()}件を中央値で補完")
                df.loc[mask, col] = df[col].median()
                df.loc[mask, "score_imputed"] = True

    # 範囲クリップ
    for col in ["attendance_rate", "midterm_score", "final_score", "assignment_rate"]:
        if col in df.columns:
            df[col] = df[col].clip(0, 100)
    if "engagement_score" in df.columns:
        df["engagement_score"] = df["engagement_score"].clip(1, 5)

    # スコア計算
    df["dropout_risk_score"] = df.apply(lambda row: calc_risk_score(row, config), axis=1)
    df["risk_category"] = df["dropout_risk_score"].apply(lambda s: classify_risk(s, config))

    # 必要列のみ保持
    keep = [c for c in df.columns if c in KEEP_COLS]
    df = df[keep]

    out_path = OUT / "cleaned_dropout_202401.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    log.info(f"出力: {out_path} ({len(df)}行)")

    # サマリー
    log.info(f"リスク分類: {df['risk_category'].value_counts().to_dict()}")
    log.info("=== cleanse.py 完了 ===")

if __name__ == "__main__":
    main()

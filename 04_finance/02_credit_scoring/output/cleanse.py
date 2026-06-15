"""
B-11: 与信スコアリング データクレンジング + スコア算出
3スタイルのCSVを統合し、正規化・与信スコア計算・リスク分類を行う。
出力: output/cleaned_credit_202401.csv
"""
import sys
import math
import logging
from pathlib import Path
import pandas as pd
import yaml

# --- パス設定 ---
BASE = Path(__file__).parent.parent
OUT = Path(__file__).parent
LOG_PATH = OUT / "cleanse.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# --- 設定読み込み ---
with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# --- カラムマッピング ---
COLUMN_MAP = {
    # application_id
    "申込ID":       "application_id",
    "ApplicationID":"application_id",
    "申込番号":     "application_id",
    # age
    "年齢":         "age",
    "Age":          "age",
    # occupation
    "職業":         "occupation",
    "Occupation":   "occupation",
    "職種":         "occupation",
    # annual_income
    "年収(万円)":   "annual_income",
    "AnnualIncome": "annual_income",
    "収入":         "annual_income",
    # years_employed
    "勤続年数(年)": "years_employed",
    "YearsEmployed":"years_employed",
    "勤務年数":     "years_employed",
    # total_debt
    "負債総額(万円)":"total_debt",
    "TotalDebt":    "total_debt",
    "負債額":       "total_debt",
    # past_delays
    "過去延滞回数": "past_delays",
    "PastDelays":   "past_delays",
    "延滞数":       "past_delays",
    # loan_amount
    "申込金額(万円)":"loan_amount",
    "LoanAmount":   "loan_amount",
    "借入希望額":   "loan_amount",
    # loan_purpose
    "申込用途":     "loan_purpose",
    "LoanPurpose":  "loan_purpose",
    "用途":         "loan_purpose",
}

# --- 職業正規化マップ ---
OCCUPATION_MAP = {
    "会社員":         "会社員",
    "Employee":       "会社員",
    "正社員":         "会社員",
    "公務員":         "公務員",
    "Government":     "公務員",
    "官公庁":         "公務員",
    "自営業":         "自営業",
    "SelfEmployed":   "自営業",
    "個人事業":       "自営業",
    "パート・アルバイト": "パート・アルバイト",
    "PartTime":       "パート・アルバイト",
    "非正規":         "パート・アルバイト",
    "無職":           "無職",
    "Unemployed":     "無職",
}


def calc_credit_score(row) -> int:
    """スコアカード方式の与信スコア計算（0〜100点、高いほど低リスク）"""
    score = 50  # ベーススコア

    # 年収（万円）
    income = row.get("annual_income", 0) or 0
    if income >= 600:
        score += 15
    elif income >= 400:
        score += 10
    elif income >= 200:
        score += 0
    elif income >= 100:
        score -= 10
    else:
        score -= 20

    # 勤続年数
    years = row.get("years_employed", 0) or 0
    if years >= 10:
        score += 10
    elif years >= 5:
        score += 5
    elif years >= 2:
        score += 0
    else:
        score -= 5

    # 負債比率（負債総額 / 年収）
    debt = row.get("total_debt", 0) or 0
    debt_ratio = debt / max(income, 1)
    if debt_ratio < 0.2:
        score += 10
    elif debt_ratio < 0.4:
        score += 5
    elif debt_ratio < 0.6:
        score -= 5
    else:
        score -= 15

    # 過去延滞回数
    delays = row.get("past_delays", 0) or 0
    if delays == 0:
        score += 10
    elif delays <= 1:
        score += 0
    elif delays <= 3:
        score -= 10
    else:
        score -= 20

    # 職業ボーナス
    occ = row.get("occupation", "")
    occ_bonus = {
        "公務員": 5,
        "会社員": 2,
        "自営業": -2,
        "パート・アルバイト": -8,
        "無職": -15,
    }.get(occ, 0)
    score += occ_bonus

    return max(0, min(100, score))


def risk_category(score: int) -> str:
    """スコアからリスク分類を返す"""
    if score < config["high_risk_threshold"]:
        return "高リスク"
    elif score < config["medium_risk_threshold"]:
        return "中リスク"
    else:
        return "低リスク"


def load_csv(path: Path) -> pd.DataFrame:
    """CSVを読み込み、カラムを正規名にリネームする"""
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    df = df.rename(columns={c: COLUMN_MAP[c] for c in df.columns if c in COLUMN_MAP})
    return df


def main():
    log.info("=== B-11 クレンジング開始 ===")

    # --- 全CSVを読み込む ---
    csv_files = sorted(BASE.glob("*.csv"))
    if not csv_files:
        log.error("入力CSVが見つかりません: %s", BASE)
        sys.exit(1)
    log.info("入力ファイル: %s", [f.name for f in csv_files])

    frames = [load_csv(f) for f in csv_files]
    df = pd.concat(frames, ignore_index=True)
    log.info("結合後行数: %d", len(df))

    # --- 型変換 ---
    numeric_cols = ["age", "annual_income", "years_employed", "total_debt", "past_delays", "loan_amount"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # --- 欠損補完フラグ ---
    impute_mask = df[numeric_cols].isnull().any(axis=1)
    df["score_imputed"] = impute_mask

    # 数値欠損を中央値で補完
    for col in numeric_cols:
        if df[col].isnull().any():
            med = df[col].median()
            n_imputed = df[col].isnull().sum()
            log.warning("欠損補完: %s → %d件 (中央値 %.1f)", col, n_imputed, med)
            df[col] = df[col].fillna(med)

    df[numeric_cols] = df[numeric_cols].astype(int)

    # --- 職業正規化 ---
    df["occupation"] = df["occupation"].map(OCCUPATION_MAP).fillna(df["occupation"])

    # --- 負数クリップ ---
    for col in ["annual_income", "total_debt", "past_delays", "loan_amount", "years_employed"]:
        df[col] = df[col].clip(lower=0)

    # --- 派生列計算 ---
    df["credit_score"] = df.apply(calc_credit_score, axis=1).astype(int)
    df["risk_category"] = df["credit_score"].apply(risk_category)
    df["debt_income_ratio"] = (df["total_debt"] / df["annual_income"].replace(0, float("nan"))).fillna(0.0).round(4)
    df["loan_income_ratio"] = (df["loan_amount"] / df["annual_income"].replace(0, float("nan"))).fillna(0.0).round(4)

    # --- 欠損率チェック ---
    imputed_ratio = df["score_imputed"].mean()
    log.info("補完率: %.2f%%", imputed_ratio * 100)
    if imputed_ratio > config["max_imputed_ratio"]:
        log.warning("補完率が閾値を超えています: %.2f%% > %.2f%%",
                    imputed_ratio * 100, config["max_imputed_ratio"] * 100)

    # --- 出力 ---
    out_path = OUT / "cleaned_credit_202401.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    log.info("出力完了: %s (%d行)", out_path, len(df))

    # --- サマリー ---
    log.info("リスク分類:\n%s", df["risk_category"].value_counts().to_string())
    log.info("平均スコア: %.1f", df["credit_score"].mean())
    log.info("=== クレンジング完了 ===")


if __name__ == "__main__":
    main()

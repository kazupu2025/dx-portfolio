"""
C-33: クレンジングスクリプト
data/ 以下の3スタイルCSVを統一フォーマットに変換し
output/cleaned_recruitment_202401.csv へ出力
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    # スタイルA (標準日本語)
    "応募日":       "apply_date",
    "応募者ID":     "applicant_id",
    "職種":         "job_type",
    "採用チャネル": "channel",
    "到達フェーズ": "reached_phase",
    "採用結果":     "hire_result",
    "選考日数":     "screening_days",
    # スタイルB (英語)
    "ApplyDate":     "apply_date",
    "ApplicantID":   "applicant_id",
    "JobType":       "job_type",
    "Channel":       "channel",
    "ReachedPhase":  "reached_phase",
    "HireResult":    "hire_result",
    "ScreeningDays": "screening_days",
    # スタイルC (バリアント日本語)
    "受付日":         "apply_date",
    "候補者番号":     "applicant_id",
    "募集職種":       "job_type",
    "応募経路":       "channel",
    "最終選考段階":   "reached_phase",
    "採否":           "hire_result",
    "選考所要日数":   "screening_days",
}

REQUIRED_COLS = [
    "apply_date", "applicant_id", "job_type", "channel",
    "reached_phase", "hire_result", "screening_days",
]

PHASE_ORDER = {
    "書類選考": 1,
    "一次面接": 2,
    "二次面接": 3,
    "最終面接": 4,
    "内定": 5,
}

VALID_JOB_TYPES = {"エンジニア", "営業", "事務", "マーケティング", "製造"}
VALID_CHANNELS = {"転職サイト", "エージェント", "リファラル", "自社HP"}
VALID_PHASES = set(PHASE_ORDER.keys())
VALID_HIRE_RESULTS = {"採用", "不採用"}


def read_csv_auto(path: Path) -> pd.DataFrame:
    """エンコーディング自動検出してCSV読み込み"""
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            raw.decode(enc)
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path)


def normalize_date(val) -> str | None:
    """YYYY-MM-DD 形式に正規化 (YYYY/MM/DD または YYYY-MM-DD を受け付ける)"""
    if pd.isna(val):
        return None
    s = str(val).strip()
    # YYYY/MM/DD -> YYYY-MM-DD
    if len(s) == 10 and s[4] == "/" and s[7] == "/":
        return s[:4] + "-" + s[5:7] + "-" + s[8:]
    # YYYY-MM-DD
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return s
    return None


def process_file(path: Path) -> pd.DataFrame:
    df = read_csv_auto(path)

    # 列名マッピング
    renamed = {col: COLUMN_MAP[str(col).strip()] for col in df.columns if str(col).strip() in COLUMN_MAP}
    df = df.rename(columns=renamed)

    # source_file 列追加
    df["source_file"] = path.name

    # 必要列だけ残す
    keep = [c for c in REQUIRED_COLS + ["source_file"] if c in df.columns]
    df = df[keep]

    # 全列 NaN 行削除
    df = df.dropna(how="all")

    # 日付正規化
    if "apply_date" in df.columns:
        df["apply_date"] = df["apply_date"].apply(normalize_date)
        df = df.dropna(subset=["apply_date"])

    # 数値列を変換
    if "screening_days" in df.columns:
        df["screening_days"] = pd.to_numeric(df["screening_days"], errors="coerce")
        df = df[df["screening_days"] > 0]

    if "applicant_id" in df.columns:
        df["applicant_id"] = pd.to_numeric(df["applicant_id"], errors="coerce").astype("Int64")

    # 無効値の除外
    if "hire_result" in df.columns:
        df = df[df["hire_result"].isin(VALID_HIRE_RESULTS)]

    if "reached_phase" in df.columns:
        df = df[df["reached_phase"].isin(VALID_PHASES)]

    # 計算列を追加
    df["is_hired"] = df["hire_result"].apply(lambda x: 1 if x == "採用" else 0)
    df["phase_order"] = df["reached_phase"].map(PHASE_ORDER)
    df["passed_first_screen"] = df["phase_order"].apply(lambda x: 1 if x >= 2 else 0)

    return df


def main():
    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if not csv_files:
        print(f"データファイルが見つかりません: {DATA_DIR}")
        return

    frames = []
    for path in csv_files:
        print(f"処理中: {path.name}")
        df = process_file(path)
        frames.append(df)
        print(f"  -> {len(df)} 行")

    result = pd.concat(frames, ignore_index=True)
    result = result.drop_duplicates()

    col_order = [
        "apply_date", "applicant_id", "job_type", "channel",
        "reached_phase", "hire_result", "screening_days",
        "is_hired", "phase_order", "passed_first_screen",
        "source_file",
    ]
    result = result[[c for c in col_order if c in result.columns]]

    out_path = OUTPUT_DIR / "cleaned_recruitment_202401.csv"
    result.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\nクレンジング完了: {len(result)} 行")
    print(f"出力: {out_path}")
    print(f"列: {list(result.columns)}")


if __name__ == "__main__":
    main()

"""
C-41: クレンジングスクリプト
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
    "応募番号":     "apply_no",
    "採用チャネル": "channel",
    "職種":         "job_type",
    "採用コスト":   "cost",
    "選考フェーズ": "phase",
    "採用可否":     "is_hired",
    "内定承諾":     "is_accepted",
    # スタイルB (英語)
    "ApplyDate":    "apply_date",
    "ApplyNo":      "apply_no",
    "Channel":      "channel",
    "JobType":      "job_type",
    "Cost":         "cost",
    "Phase":        "phase",
    "IsHired":      "is_hired",
    "IsAccepted":   "is_accepted",
    # スタイルC (バリアント日本語)
    "日付":         "apply_date",
    "管理番号":     "apply_no",
    "チャネル":     "channel",
    "職種区分":     "job_type",
    "コスト":       "cost",
    "フェーズ":     "phase",
    "採否":         "is_hired",
    "承諾":         "is_accepted",
}

REQUIRED_COLS = [
    "apply_date", "apply_no", "channel", "job_type",
    "cost", "phase", "is_hired", "is_accepted",
]

VALID_CHANNELS = {"求人サイト", "SNS採用", "リファラル", "エージェント", "合同説明会"}
VALID_JOB_TYPES = {"エンジニア", "営業", "事務", "マーケ", "デザイン"}
VALID_PHASES = {"書類選考", "一次面接", "二次面接", "最終面接", "内定"}

HIGH_EFFICIENCY_CHANNELS = {"リファラル", "SNS採用"}


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

    # 日付正規化: スラッシュをダッシュに変換してから pd.to_datetime
    if "apply_date" in df.columns:
        df["apply_date"] = df["apply_date"].astype(str).str.replace("/", "-", regex=False)
        df["apply_date"] = pd.to_datetime(df["apply_date"], format="%Y-%m-%d", errors="coerce")
        df = df.dropna(subset=["apply_date"])
        df["apply_date"] = df["apply_date"].dt.strftime("%Y-%m-%d")

    # 数値変換
    if "cost" in df.columns:
        df["cost"] = pd.to_numeric(df["cost"], errors="coerce")
        df = df[df["cost"] > 0]

    if "apply_no" in df.columns:
        df["apply_no"] = pd.to_numeric(df["apply_no"], errors="coerce").astype("Int64")

    if "is_hired" in df.columns:
        df["is_hired"] = pd.to_numeric(df["is_hired"], errors="coerce")
        df = df[df["is_hired"].isin([0, 1])]
        df["is_hired"] = df["is_hired"].astype(int)

    if "is_accepted" in df.columns:
        df["is_accepted"] = pd.to_numeric(df["is_accepted"], errors="coerce")

    # 無効値の除外
    if "channel" in df.columns:
        df = df[df["channel"].isin(VALID_CHANNELS)]

    if "job_type" in df.columns:
        df = df[df["job_type"].isin(VALID_JOB_TYPES)]

    if "phase" in df.columns:
        df = df[df["phase"].isin(VALID_PHASES)]

    return df


def add_computed_columns(df: pd.DataFrame) -> pd.DataFrame:
    """計算列を追加"""
    # cost_per_hire: 採用コスト（採否によらず）
    df["cost_per_hire"] = df["cost"]

    # channel_efficiency: 高効率チャネル かつ コスト <= 中央値
    cost_median = df["cost"].median()
    df["channel_efficiency"] = df.apply(
        lambda row: "高効率"
        if row["channel"] in HIGH_EFFICIENCY_CHANNELS and row["cost"] <= cost_median
        else "標準",
        axis=1,
    )

    # offer_acceptance
    def _offer_acceptance(row):
        if row["is_hired"] == 1 and row["is_accepted"] == 1:
            return "承諾"
        elif row["is_hired"] == 1 and row["is_accepted"] == 0:
            return "辞退"
        else:
            return "該当なし"

    df["offer_acceptance"] = df.apply(_offer_acceptance, axis=1)

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

    result = add_computed_columns(result)

    col_order = [
        "apply_date", "apply_no", "channel", "job_type",
        "cost", "phase", "is_hired", "is_accepted",
        "cost_per_hire", "channel_efficiency", "offer_acceptance",
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

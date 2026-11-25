# cleanse.py — データクレンジングモジュール（C-36 顧客満足度）
# encoding: utf-8

import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "cleaned_satisfaction_202401.csv"

# ── 列名マッピング（3スタイルを正規名に統一）──────────────────────────────
COLUMN_MAP = {
    # スタイルA（標準日本語）
    "回答日": "response_date",
    "顧客コード": "customer_code",
    "サービス区分": "service_type",
    "担当者": "agent",
    "総合満足度": "overall_sat",
    "対応速度": "response_speed",
    "品質": "quality",
    "コスパ": "cost_perf",
    "推奨度": "nps",
    # スタイルB（英語）
    "ResponseDate": "response_date",
    "CustomerCode": "customer_code",
    "ServiceType": "service_type",
    "Agent": "agent",
    "OverallSat": "overall_sat",
    "ResponseSpeed": "response_speed",
    "Quality": "quality",
    "CostPerf": "cost_perf",
    "NPS": "nps",
    # スタイルC（バリアント日本語）
    "調査日": "response_date",
    "顧客ID": "customer_code",
    "サービス種別": "service_type",
    "対応者": "agent",
    "総合評価": "overall_sat",
    "速度評価": "response_speed",
    "品質評価": "quality",
    "費用対効果": "cost_perf",
    "NPS推奨": "nps",
}

REQUIRED_COLS = [
    "response_date", "customer_code", "service_type", "agent",
    "overall_sat", "response_speed", "quality", "cost_perf", "nps",
]


def _parse_date(date_str: str) -> str:
    """YYYY/MM/DD または YYYY-MM-DD を YYYY-MM-DD に統一する。"""
    s = str(date_str).strip()
    if "/" in s:
        parts = s.split("/")
        return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
    return s


def _nps_category(nps: int) -> str:
    if nps >= 9:
        return "推奨者"
    elif nps >= 7:
        return "中立者"
    return "批判者"


def _satisfaction_flag(csat: float) -> str:
    if csat >= 4.0:
        return "満足"
    elif csat >= 3.0:
        return "普通"
    return "不満"


def load_and_cleanse(csv_path: Path) -> pd.DataFrame:
    """単一 CSV を読み込み、列名正規化・計算列付与を行う。"""
    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    # 列名マッピング
    df = df.rename(columns={c: COLUMN_MAP.get(c, c) for c in df.columns})

    # 不足列があれば NaN で補完（バリデーションで後ほど検出）
    for col in REQUIRED_COLS:
        if col not in df.columns:
            df[col] = pd.NA

    # 日付正規化
    df["response_date"] = df["response_date"].apply(_parse_date)

    # 数値型変換
    for col in ["overall_sat", "response_speed", "quality", "cost_perf", "nps"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 計算列
    df["csat_score"] = (
        df["overall_sat"] + df["response_speed"] + df["quality"] + df["cost_perf"]
    ) / 4

    df["nps_category"] = df["nps"].apply(
        lambda x: _nps_category(int(x)) if pd.notna(x) else pd.NA
    )
    df["satisfaction_flag"] = df["csat_score"].apply(
        lambda x: _satisfaction_flag(float(x)) if pd.notna(x) else pd.NA
    )

    # ソースファイル列
    df["source_file"] = csv_path.name

    return df


def run() -> pd.DataFrame:
    """data/ 以下の全 CSV を結合・クレンジングして output に保存する。"""
    csv_files = sorted(DATA_DIR.glob("satisfaction_*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {DATA_DIR}")

    frames = [load_and_cleanse(f) for f in csv_files]
    df = pd.concat(frames, ignore_index=True)

    # 最終列順を整理
    base_cols = REQUIRED_COLS + ["csat_score", "nps_category", "satisfaction_flag", "source_file"]
    df = df[[c for c in base_cols if c in df.columns]]

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"Cleansed data saved: {OUTPUT_FILE} ({len(df)} rows)")
    return df


if __name__ == "__main__":
    run()

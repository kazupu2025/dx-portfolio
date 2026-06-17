"""
C-39: 入居者対応履歴・クレーム集計パイプライン
クレンジングスクリプト
3スタイルのCSVを統一正規化し output/cleaned_claims_202401.csv に出力する
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# 各スタイルの列名 -> 正規名マッピング
COLUMN_MAP = {
    # スタイルA: 標準日本語列名
    "受付日": "receipt_date",
    "案件番号": "case_no",
    "物件名": "property_name",
    "部屋番号": "room_no",
    "クレーム区分": "claim_type",
    "対応状況": "status",
    "対応日数": "response_days",
    "対応工数（時間）": "work_hours",
    # スタイルB: 英語列名
    "ReceiptDate": "receipt_date",
    "CaseNo": "case_no",
    "PropertyName": "property_name",
    "RoomNo": "room_no",
    "ClaimType": "claim_type",
    "Status": "status",
    "ResponseDays": "response_days",
    "WorkHours": "work_hours",
    # スタイルC: バリアント日本語列名
    "日付": "receipt_date",
    "管理番号": "case_no",
    "建物名": "property_name",
    "号室": "room_no",
    "種別": "claim_type",
    "状況": "status",
    "処理日数": "response_days",
    "工数": "work_hours",
}

REQUIRED_COLS = [
    "receipt_date", "case_no", "property_name", "room_no",
    "claim_type", "status", "response_days", "work_hours",
]

UNIT_PRICE = 5000  # 円/時間


def load_and_normalize(filepath: Path) -> pd.DataFrame:
    """CSVを読み込み、列名を正規化して返す"""
    df = pd.read_csv(filepath, encoding="utf-8-sig", dtype=str)
    df = df.rename(columns=COLUMN_MAP)
    df["source_file"] = filepath.name
    return df


def normalize_date(series: pd.Series) -> pd.Series:
    """日付をYYYY-MM-DD形式に統一する（スラッシュをダッシュに変換してからパース）"""
    normalized = series.str.strip().str.replace("/", "-", regex=False)
    return pd.to_datetime(normalized, format="%Y-%m-%d", errors="coerce").dt.strftime("%Y-%m-%d")


def add_calculated_columns(df: pd.DataFrame) -> pd.DataFrame:
    """計算列を追加する"""
    df["response_days"] = pd.to_numeric(df["response_days"], errors="coerce")
    df["work_hours"] = pd.to_numeric(df["work_hours"], errors="coerce")

    # is_resolved: 解決済なら1、それ以外なら0
    df["is_resolved"] = (df["status"] == "解決済").astype(int)

    # urgency: 緊急・通常・遅延の3区分
    urgent_types = {"水漏れ", "設備故障"}

    def calc_urgency(row):
        if row["claim_type"] in urgent_types and row["status"] != "解決済":
            return "緊急"
        elif row["response_days"] <= 7:
            return "通常"
        else:
            return "遅延"

    df["urgency"] = df.apply(calc_urgency, axis=1)

    # cost_estimate: 工数 × 単価5000円
    df["cost_estimate"] = df["work_hours"] * UNIT_PRICE

    return df


def cleanse():
    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {DATA_DIR}")

    frames = []
    for fp in csv_files:
        df = load_and_normalize(fp)
        # 必須列が揃っているか確認
        missing = [c for c in REQUIRED_COLS if c not in df.columns]
        if missing:
            print(f"[WARN] {fp.name}: missing columns after mapping: {missing}")
            continue
        df = df[REQUIRED_COLS + ["source_file"]]
        frames.append(df)
        print(f"[OK] Loaded: {fp.name} ({len(df)} rows)")

    if not frames:
        raise ValueError("No valid CSV files could be loaded.")

    combined = pd.concat(frames, ignore_index=True)

    # 日付の正規化
    combined["receipt_date"] = normalize_date(combined["receipt_date"])

    # 型変換
    combined["response_days"] = pd.to_numeric(combined["response_days"], errors="coerce")
    combined["work_hours"] = pd.to_numeric(combined["work_hours"], errors="coerce")

    # 計算列の追加
    combined = add_calculated_columns(combined)

    output_path = OUTPUT_DIR / "cleaned_claims_202401.csv"
    combined.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\n[DONE] Cleaned data saved: {output_path} ({len(combined)} rows)")
    return combined


if __name__ == "__main__":
    cleanse()

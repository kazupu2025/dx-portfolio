# -*- coding: utf-8 -*-
"""
C-34 返品・クレームデータ集計レポートパイプライン
クレンジングスクリプト

3スタイルのCSVを読み込み、正規化して output/cleaned_claims_202401.csv に出力する。
"""

import pandas as pd
from pathlib import Path

# ---- 列名マッピング -------------------------------------------------------
COLUMN_MAP = {
    # スタイルA（標準日本語）
    "受付日": "receipt_date",
    "案件番号": "case_no",
    "店舗名": "store_name",
    "商品カテゴリ": "category",
    "クレーム区分": "claim_type",
    "返品金額": "return_amount",
    "対応日数": "response_days",
    "解決フラグ": "resolved_flag",
    # スタイルB（英語）
    "ReceiptDate": "receipt_date",
    "CaseNo": "case_no",
    "StoreName": "store_name",
    "Category": "category",
    "ClaimType": "claim_type",
    "ReturnAmount": "return_amount",
    "ResponseDays": "response_days",
    "ResolvedFlag": "resolved_flag",
    # スタイルC（バリアント日本語）
    "日付": "receipt_date",
    "受付番号": "case_no",
    "店舗": "store_name",
    "品目区分": "category",
    "理由区分": "claim_type",
    "返金額": "return_amount",
    "処理日数": "response_days",
    "完了フラグ": "resolved_flag",
}

CANONICAL_COLUMNS = [
    "receipt_date",
    "case_no",
    "store_name",
    "category",
    "claim_type",
    "return_amount",
    "response_days",
    "resolved_flag",
]


def normalize_date(series: pd.Series) -> pd.Series:
    """YYYY/MM/DD または YYYY-MM-DD を YYYY-MM-DD に統一する。"""
    return pd.to_datetime(series, format="mixed", dayfirst=False).dt.strftime("%Y-%m-%d")


def add_response_level(response_days: pd.Series) -> pd.Series:
    """対応スピードを 迅速/標準/遅延 に分類する。"""
    def classify(days: int) -> str:
        if days <= 3:
            return "迅速"
        elif days <= 10:
            return "標準"
        else:
            return "遅延"

    return response_days.apply(classify)


def load_csv(filepath: Path) -> pd.DataFrame:
    """CSVを読み込み、列名を正規化して返す。"""
    try:
        df = pd.read_csv(filepath, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(filepath, encoding="utf-8")

    df = df.rename(columns=COLUMN_MAP)
    missing = [c for c in CANONICAL_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"[ERROR] {filepath.name} に必須列が不足: {missing}")

    df = df[CANONICAL_COLUMNS].copy()
    df["source_file"] = filepath.name
    return df


def cleanse(df: pd.DataFrame) -> pd.DataFrame:
    """クレンジング処理を適用して返す。"""
    # 日付正規化
    df["receipt_date"] = normalize_date(df["receipt_date"])

    # 数値型変換
    df["return_amount"] = pd.to_numeric(df["return_amount"], errors="coerce").fillna(0).astype(int)
    df["response_days"] = pd.to_numeric(df["response_days"], errors="coerce").fillna(1).astype(int)
    df["resolved_flag"] = pd.to_numeric(df["resolved_flag"], errors="coerce").fillna(0).astype(int)

    # 文字列クレンジング
    for col in ["store_name", "category", "claim_type"]:
        df[col] = df[col].astype(str).str.strip()

    # 計算列の追加
    df["is_resolved"] = df["resolved_flag"].apply(lambda x: 1 if x == 1 else 0).astype(int)
    df["response_level"] = add_response_level(df["response_days"])

    return df


def main() -> None:
    base_dir = Path(__file__).parent
    data_dir = base_dir / "data"
    output_dir = base_dir / "output"
    output_dir.mkdir(exist_ok=True)

    csv_files = sorted(data_dir.glob("claims_style*.csv"))
    if not csv_files:
        print("[ERROR] data/ に CSVファイルが見つかりません。_gen_sample_data.py を先に実行してください。")
        return

    frames = []
    for filepath in csv_files:
        print(f"[LOAD] {filepath.name}")
        df = load_csv(filepath)
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    cleaned = cleanse(combined)

    out_path = output_dir / "cleaned_claims_202401.csv"
    cleaned.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[DONE] {out_path}  ({len(cleaned)} rows)")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
C-52: 保険契約問い合わせ・対応履歴分析パイプライン クレンジングスクリプト
3スタイルのCSVを正規化して output/cleaned_inquiries_202401.csv に出力する。
"""
import pandas as pd
import numpy as np
from pathlib import Path

random_imported = False

BASE = Path(__file__).parent
DATA_DIR = BASE / "data"
OUTPUT_DIR = BASE / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 3スタイル -> 正規列名へのマッピング
COLUMN_MAP = {
    # StyleA (標準日本語)
    "問い合わせ日":       "inquiry_date",
    "問い合わせID":       "inquiry_id",
    "問い合わせ区分":     "inquiry_type",
    "チャネル":           "channel",
    "担当者ID":           "operator_id",
    "対応時間(分)":       "handling_minutes",
    "解決フラグ":         "is_resolved",
    "再問い合わせフラグ": "recontact_flag",
    "満足度":             "satisfaction",
    # StyleB (English)
    "InquiryDate":    "inquiry_date",
    "InquiryID":      "inquiry_id",
    "InquiryType":    "inquiry_type",
    "Channel":        "channel",
    "OperatorID":     "operator_id",
    "HandlingMinutes": "handling_minutes",
    "IsResolved":     "is_resolved",
    "RecontactFlag":  "recontact_flag",
    "Satisfaction":   "satisfaction",
    # StyleC (バリアント日本語)
    "受付日":       "inquiry_date",
    "受付番号":     "inquiry_id",
    "区分":         "inquiry_type",
    "受付チャネル": "channel",
    "対応者":       "operator_id",
    "処理時間":     "handling_minutes",
    "解決":         "is_resolved",
    "再連絡":       "recontact_flag",
    "CS評価":       "satisfaction",
}

# 問い合わせ区分の正規化マッピング
TYPE_MAP = {
    # StyleA
    "契約内容確認": "契約内容確認",
    "保険金請求":   "保険金請求",
    "解約手続き":   "解約手続き",
    "新規加入":     "新規加入",
    "変更手続き":   "変更手続き",
    # StyleB (English)
    "ContractConfirm":  "契約内容確認",
    "ClaimRequest":     "保険金請求",
    "Cancellation":     "解約手続き",
    "NewEnrollment":    "新規加入",
    "ChangeRequest":    "変更手続き",
    # StyleC (バリアント)
    "契約照会":   "契約内容確認",
    "給付請求":   "保険金請求",
    "解約":       "解約手続き",
    "新規契約":   "新規加入",
    "契約変更":   "変更手続き",
}

# チャネルの正規化マッピング
CHANNEL_MAP = {
    "電話": "電話", "Phone": "電話", "TEL": "電話",
    "メール": "メール", "Email": "メール", "Mail": "メール",
    "窓口": "窓口", "Counter": "窓口", "来店": "窓口",
}

CANONICAL_COLS = [
    "inquiry_date", "inquiry_id", "inquiry_type", "channel", "operator_id",
    "handling_minutes", "is_resolved", "recontact_flag", "satisfaction",
    "efficiency_flag", "cs_grade", "source_file",
]


def normalize_date(val) -> str:
    if pd.isna(val) or str(val).strip() == "":
        return None
    s = str(val).strip().replace("/", "-")
    try:
        return pd.to_datetime(s, format="%Y-%m-%d").strftime("%Y-%m-%d")
    except Exception:
        pass
    try:
        return pd.to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        return None


def compute_efficiency_flag(minutes) -> str:
    try:
        m = float(minutes)
    except (TypeError, ValueError):
        return None
    if m <= 30:
        return "迅速"
    elif m <= 60:
        return "標準"
    else:
        return "長時間"


def compute_cs_grade(satisfaction) -> str:
    try:
        s = float(satisfaction)
    except (TypeError, ValueError):
        return None
    if s >= 4:
        return "高満足"
    elif s >= 3:
        return "普通"
    else:
        return "低満足"


def read_csv_auto(path: Path) -> pd.DataFrame:
    raw = path.read_bytes()
    for enc in ["utf-8-sig", "utf-8", "cp932"]:
        try:
            raw.decode(enc)
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path, encoding="utf-8", errors="replace")


all_frames = []
csv_files = sorted(DATA_DIR.glob("*.csv"))

if not csv_files:
    csv_files = sorted(BASE.glob("*.csv"))

for f in csv_files:
    try:
        df = read_csv_auto(f)
    except Exception as e:
        print(f"[WARN] {f.name} read error: {e}")
        continue

    # 列名の正規化
    renamed = {}
    for col in df.columns:
        col_str = str(col).strip()
        if col_str in COLUMN_MAP:
            renamed[col] = COLUMN_MAP[col_str]
        elif str(col).startswith("Unnamed"):
            renamed[col] = f"_drop_{col}"
    df = df.rename(columns=renamed)

    # 不要列削除
    drop_cols = [c for c in df.columns if str(c).startswith("_drop_")]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    df = df.dropna(how="all")

    # 問い合わせ区分正規化
    if "inquiry_type" in df.columns:
        df["inquiry_type"] = df["inquiry_type"].map(TYPE_MAP).fillna(df["inquiry_type"])

    # チャネル正規化
    if "channel" in df.columns:
        df["channel"] = df["channel"].map(CHANNEL_MAP).fillna(df["channel"])

    # 数値変換
    for col in ["handling_minutes", "is_resolved", "recontact_flag", "satisfaction"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 日付正規化
    if "inquiry_date" in df.columns:
        df["inquiry_date"] = df["inquiry_date"].apply(normalize_date)

    # 派生列
    if "handling_minutes" in df.columns:
        df["efficiency_flag"] = df["handling_minutes"].apply(compute_efficiency_flag)
    if "satisfaction" in df.columns:
        df["cs_grade"] = df["satisfaction"].apply(compute_cs_grade)

    df["source_file"] = f.name

    # 必要列のみ保持
    keep = [c for c in CANONICAL_COLS if c in df.columns]
    df = df[keep]

    all_frames.append(df)
    print(f"[OK] {f.name}: {len(df)} rows")

if all_frames:
    result = pd.concat(all_frames, ignore_index=True)
    result = result.drop_duplicates(subset=["inquiry_id"], keep="first")

    col_order = [c for c in CANONICAL_COLS if c in result.columns]
    result = result[col_order]

    out_path = OUTPUT_DIR / "cleaned_inquiries_202401.csv"
    result.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n[OK] Cleansing complete: {len(result)} rows -> {out_path}")
    print(f"     source_file types: {result['source_file'].nunique()}")
    print(f"     efficiency_flag distribution:\n{result['efficiency_flag'].value_counts().to_string()}")
    print(f"     cs_grade distribution:\n{result['cs_grade'].value_counts().to_string()}")
else:
    print("[FAIL] No target CSV found")
    print(f"       Check data/ directory: {DATA_DIR}")

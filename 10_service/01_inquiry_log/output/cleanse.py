"""
B-15 問い合わせログ クレンジングスクリプト
- 3スタイルCSVを統合
- キーワードベース自動カテゴリ分類
- 対応時間(response_minutes)計算
"""
import sys
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
import yaml

BASE = Path(__file__).resolve().parent.parent
OUT  = Path(__file__).resolve().parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(OUT / "cleanse.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# --- 設定 ---
with open(BASE / "config.yml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

COLUMN_MAP = {
    "問い合わせID":   "inquiry_id",   "InquiryID":   "inquiry_id",   "受付番号": "inquiry_id",
    "受付日時":       "received_at",  "ReceivedAt":  "received_at",
    "完了日時":       "completed_at", "CompletedAt": "completed_at", "対応完了時刻": "completed_at",
    "担当者ID":       "operator_id",  "OperatorID":  "operator_id",  "担当者コード": "operator_id",
    "担当者名":       "operator_name","OperatorName":"operator_name","担当者": "operator_name",
    "チャネル":       "channel",      "Channel":     "channel",      "受付チャネル": "channel",
    "問い合わせ内容": "inquiry_text", "InquiryKeyword":"inquiry_text","問い合わせ種別": "inquiry_text",
    "カテゴリ":       "category",     "Category":    "category",     "分類": "category",
    "解決状況":       "resolution",   "ResolutionStatus":"resolution","対応結果": "resolution",
    "エスカレーション":"escalation",  "Escalation":  "escalation",   "上位エスカレ": "escalation",
}

RESOLUTION_MAP = {
    "解決済": "解決済", "Resolved": "解決済", "解決": "解決済",
    "対応中": "対応中", "InProgress": "対応中",
    "未解決": "未解決", "Unresolved": "未解決", "未対応": "未解決",
    "エスカレ済": "エスカレ済", "Escalated": "エスカレ済", "エスカレ": "エスカレ済",
}

CHANNEL_MAP = {
    "電話": "電話", "Phone": "電話",
    "メール": "メール", "Email": "メール",
    "チャット": "チャット", "Chat": "チャット",
    "SNS": "SNS",
}

CATEGORY_KEYWORDS = {
    "請求・支払い": ["請求", "支払い", "課金", "料金", "invoice", "payment", "billing", "charge"],
    "製品不具合":   ["壊れ", "故障", "動かない", "エラー", "バグ", "不具合", "broken", "error", "defect", "malfunction"],
    "使い方・操作方法": ["使い方", "操作", "方法", "やり方", "how to", "how do", "usage", "tutorial", "設定"],
    "配送・到着":   ["配送", "到着", "届かない", "遅延", "追跡", "delivery", "shipping", "tracking", "arrived"],
    "返品・交換":   ["返品", "交換", "キャンセル", "返金", "return", "refund", "exchange", "cancel"],
}

KEEP_COLS = {
    "inquiry_id", "received_at", "completed_at",
    "operator_id", "operator_name", "channel",
    "inquiry_text", "category", "resolution",
    "escalation", "response_minutes", "is_resolved", "is_escalated",
    "source_file",
}

def classify_inquiry(text: str) -> str:
    if pd.isna(text) or str(text).strip() == "":
        return "その他"
    text_lower = str(text).lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw.lower() in text_lower for kw in keywords):
            return category
    return "その他"

def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    df = df.rename(columns={c: COLUMN_MAP[c] for c in df.columns if c in COLUMN_MAP})
    df["source_file"] = path.name
    return df

def parse_datetime(series: pd.Series) -> pd.Series:
    """Parse datetime with multiple format attempts."""
    for fmt in ["%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
        try:
            parsed = pd.to_datetime(series, format=fmt, errors="coerce")
            if parsed.notna().sum() > len(series) * 0.8:
                return parsed
        except Exception:
            pass
    return pd.to_datetime(series, errors="coerce")

def main():
    log.info("=== B-15 クレンジング開始 ===")

    csv_files = sorted(BASE.glob("*.csv"))
    log.info(f"CSVファイル数: {len(csv_files)}")

    frames = []
    for p in csv_files:
        df = load_csv(p)
        log.info(f"  読込: {p.name} → {len(df)}行")
        frames.append(df)

    df = pd.concat(frames, ignore_index=True)
    log.info(f"結合後: {len(df)}行")

    # datetime変換
    df["received_at"]  = parse_datetime(df["received_at"])
    df["completed_at"] = parse_datetime(df["completed_at"])

    # response_minutes計算
    df["response_minutes"] = ((df["completed_at"] - df["received_at"]).dt.total_seconds() / 60).round().astype("Int64")

    # 負・0補完（メジアンで補完）
    valid_mask = df["response_minutes"] > 0
    median_minutes = int(df.loc[valid_mask, "response_minutes"].median())
    bad_count = (~valid_mask).sum()
    if bad_count > 0:
        log.warning(f"response_minutes<=0: {bad_count}件 → メジアン({median_minutes}分)で補完")
        df.loc[~valid_mask, "response_minutes"] = median_minutes

    # datetime → 文字列（YYYY-MM-DD HH:MM形式）
    df["received_at"]  = df["received_at"].dt.strftime("%Y-%m-%d %H:%M")
    df["completed_at"] = df["completed_at"].dt.strftime("%Y-%m-%d %H:%M")

    # resolution正規化
    df["resolution"] = df["resolution"].map(RESOLUTION_MAP).fillna("未解決")

    # channel正規化
    df["channel"] = df["channel"].map(CHANNEL_MAP).fillna("その他")

    # escalation → int
    df["escalation"] = pd.to_numeric(df["escalation"], errors="coerce").fillna(0).astype(int)

    # カテゴリ自動分類（全件強制分類）
    df["category"] = df["inquiry_text"].apply(classify_inquiry)

    # 派生列
    df["is_resolved"]  = (df["resolution"] == "解決済").astype(int)
    df["is_escalated"] = (df["escalation"] == 1).astype(int)

    # 不要列除去
    drop_cols = [c for c in df.columns if c not in KEEP_COLS]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    out_path = OUT / "cleaned_inquiry_202401.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    log.info(f"出力: {out_path} ({len(df)}行)")

    # サマリーログ
    log.info(f"カテゴリ分布:\n{df['category'].value_counts().to_string()}")
    log.info(f"解決状況分布:\n{df['resolution'].value_counts().to_string()}")
    log.info(f"チャネル分布:\n{df['channel'].value_counts().to_string()}")
    log.info(f"担当者数: {df['operator_id'].nunique()}")
    log.info(f"平均対応時間: {df['response_minutes'].mean():.1f}分")
    log.info("=== クレンジング完了 ===")

if __name__ == "__main__":
    main()

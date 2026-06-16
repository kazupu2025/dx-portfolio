"""
C-26: 請求書突合・差異検出パイプライン クレンジングスクリプト
3スタイルのCSVを正規化して output/cleaned_invoice_202401.csv に出力する。
"""
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent
DATA_DIR = BASE / "data"
OUTPUT_DIR = BASE / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 3スタイル → 正規列名へのマッピング
COLUMN_MAP = {
    # スタイルA（標準日本語）
    "請求書番号": "invoice_no",
    "請求日":     "invoice_date",
    "得意先コード": "client_code",
    "請求金額":   "invoice_amount",
    "入金金額":   "received_amount",
    "入金日":     "received_date",
    "支払区分":   "payment_type",
    # スタイルB（英語）
    "InvoiceNo":      "invoice_no",
    "InvoiceDate":    "invoice_date",
    "ClientCode":     "client_code",
    "InvoiceAmount":  "invoice_amount",
    "ReceivedAmount": "received_amount",
    "ReceivedDate":   "received_date",
    "PaymentType":    "payment_type",
    # スタイルC（バリアント日本語）
    "伝票番号":  "invoice_no",
    "発行日":    "invoice_date",
    "取引先CD": "client_code",
    "請求額":   "invoice_amount",
    "受領額":   "received_amount",
    "受取日":   "received_date",
    "決済方法": "payment_type",
}

# 支払区分の正規化マッピング
PAYMENT_MAP = {
    "銀行振込": "銀行振込", "BankTransfer": "銀行振込", "振込": "銀行振込",
    "口座振替": "口座振替", "DirectDebit": "口座振替", "自動振替": "口座振替",
    "手形": "手形", "Bill": "手形", "約束手形": "手形",
}

CANONICAL_COLS = [
    "invoice_no", "invoice_date", "client_code", "invoice_amount",
    "received_amount", "received_date", "payment_type",
    "variance_amount", "variance_rate", "match_status", "source_file",
]


def normalize_date(val) -> str | None:
    if pd.isna(val) or str(val).strip() == "":
        return None
    s = str(val).strip()
    for fmt in ["%Y/%m/%d", "%Y-%m-%d", "%Y年%m月%d日", "%m/%d/%Y"]:
        try:
            return pd.to_datetime(s, format=fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    try:
        return pd.to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        return None


def normalize_numeric(val) -> float | None:
    if pd.isna(val) or str(val).strip() in ("", "-", "NULL", "N/A"):
        return None
    s = (str(val).strip()
         .replace(",", "").replace("，", "")
         .replace("円", "").strip())
    s = s.translate(str.maketrans("０１２３４５６７８９．", "0123456789."))
    try:
        return float(s)
    except ValueError:
        return None


def compute_match_status(rec: float, inv: float) -> str:
    variance = rec - inv
    if abs(variance) <= 1:
        return "一致"
    if rec == 0:
        return "未入金"
    if variance > 1:
        return "過払"
    return "差異"


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
    # フォールバック: スクリプトと同じディレクトリ内のCSVも探す
    csv_files = sorted(BASE.glob("*.csv"))

for f in csv_files:
    try:
        df = read_csv_auto(f)
    except Exception as e:
        print(f"[WARN] {f.name} 読み込みエラー: {e}")
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

    # 数値正規化
    for col in ["invoice_amount", "received_amount"]:
        if col in df.columns:
            df[col] = df[col].apply(normalize_numeric).fillna(0)

    # 日付正規化
    for col in ["invoice_date", "received_date"]:
        if col in df.columns:
            df[col] = df[col].apply(normalize_date)

    # 支払区分の正規化
    if "payment_type" in df.columns:
        df["payment_type"] = df["payment_type"].map(PAYMENT_MAP).fillna(df["payment_type"])

    # 計算列追加
    if "invoice_amount" in df.columns and "received_amount" in df.columns:
        df["variance_amount"] = df["received_amount"] - df["invoice_amount"]
        inv_safe = df["invoice_amount"].replace(0, float("nan"))
        df["variance_rate"] = (df["variance_amount"] / inv_safe).round(4)
        df["match_status"] = df.apply(
            lambda r: compute_match_status(r["received_amount"], r["invoice_amount"]),
            axis=1,
        )

    df["source_file"] = f.name

    # 必要列のみ保持
    keep = [c for c in CANONICAL_COLS if c in df.columns]
    df = df[keep]

    all_frames.append(df)
    print(f"[OK] {f.name}: {len(df)} 行")

if all_frames:
    result = pd.concat(all_frames, ignore_index=True)
    result = result.drop_duplicates(subset=["invoice_no"], keep="first")

    # 列順序を整える
    col_order = [c for c in CANONICAL_COLS if c in result.columns]
    result = result[col_order]

    out_path = OUTPUT_DIR / "cleaned_invoice_202401.csv"
    result.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n[OK] クレンジング完了: {len(result)} 行 -> {out_path}")
    print(f"     source_file 種類: {result['source_file'].nunique()}")
    print(f"     match_status 内訳:\n{result['match_status'].value_counts().to_string()}")
else:
    print("[FAIL] 処理対象CSVが見つかりませんでした")
    print(f"       data/ ディレクトリを確認: {DATA_DIR}")

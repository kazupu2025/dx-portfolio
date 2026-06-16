"""
C-31: 契約更新アラート・期限管理パイプライン クレンジングスクリプト
3スタイルのCSVを正規化して output/cleaned_contracts_202401.csv に出力する。
基準日: 2024-02-01
"""
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent
DATA_DIR = BASE / "data"
OUTPUT_DIR = BASE / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 基準日
REFERENCE_DATE = pd.Timestamp("2024-02-01")

# 保険種別の正規化マッピング
INSURANCE_MAP = {
    # スタイルA（日本語）
    "生命保険": "生命保険",
    "損害保険": "損害保険",
    "医療保険": "医療保険",
    "年金保険": "年金保険",
    # スタイルB（英語）
    "Life":     "生命保険",
    "Property": "損害保険",
    "Medical":  "医療保険",
    "Annuity":  "年金保険",
    # スタイルC（バリアント日本語）
    "生命": "生命保険",
    "損害": "損害保険",
    "医療": "医療保険",
    "年金": "年金保険",
}

# 3スタイル -> 正規列名へのマッピング
COLUMN_MAP = {
    # スタイルA（標準日本語）
    "契約番号":   "contract_no",
    "顧客コード": "customer_code",
    "保険種別":   "insurance_type",
    "契約開始日": "start_date",
    "契約終了日": "end_date",
    "年間保険料": "annual_premium",
    "担当者":     "agent_name",
    # スタイルB（英語）
    "ContractNo":     "contract_no",
    "CustomerCode":   "customer_code",
    "InsuranceType":  "insurance_type",
    "StartDate":      "start_date",
    "EndDate":        "end_date",
    "AnnualPremium":  "annual_premium",
    "AgentName":      "agent_name",
    # スタイルC（バリアント日本語）
    "証券番号":  "contract_no",
    "顧客ID":   "customer_code",
    "商品区分":  "insurance_type",
    "開始日":   "start_date",
    "満期日":   "end_date",
    "年払保険料": "annual_premium",
    "担当営業":  "agent_name",
}

CANONICAL_COLS = [
    "contract_no", "customer_code", "insurance_type",
    "start_date", "end_date", "annual_premium", "agent_name",
    "days_to_expiry", "renewal_status", "contract_years", "source_file",
]


def normalize_date(val) -> str | None:
    if pd.isna(val) or str(val).strip() == "":
        return None
    s = str(val).strip()
    for fmt in ["%Y/%m/%d", "%Y-%m-%d", "%Y年%m月%d日"]:
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


def compute_renewal_status(days: float) -> str:
    if pd.isna(days):
        return "不明"
    if days < 0:
        return "期限切れ"
    elif days <= 30:
        return "緊急"
    elif days <= 90:
        return "警告"
    else:
        return "正常"


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
    if "annual_premium" in df.columns:
        df["annual_premium"] = df["annual_premium"].apply(normalize_numeric)

    # 日付正規化
    for col in ["start_date", "end_date"]:
        if col in df.columns:
            df[col] = df[col].apply(normalize_date)

    # 保険種別の正規化
    if "insurance_type" in df.columns:
        df["insurance_type"] = df["insurance_type"].map(INSURANCE_MAP).fillna(df["insurance_type"])

    # 計算列追加
    if "end_date" in df.columns:
        end_dt = pd.to_datetime(df["end_date"], errors="coerce")
        df["days_to_expiry"] = (end_dt - REFERENCE_DATE).dt.days
        df["renewal_status"] = df["days_to_expiry"].apply(compute_renewal_status)

    if "start_date" in df.columns and "end_date" in df.columns:
        start_dt = pd.to_datetime(df["start_date"], errors="coerce")
        end_dt2 = pd.to_datetime(df["end_date"], errors="coerce")
        df["contract_years"] = ((end_dt2 - start_dt).dt.days / 365).round(2)

    df["source_file"] = f.name

    # 必要列のみ保持
    keep = [c for c in CANONICAL_COLS if c in df.columns]
    df = df[keep]

    all_frames.append(df)
    print(f"[OK] {f.name}: {len(df)} 行")

if all_frames:
    result = pd.concat(all_frames, ignore_index=True)
    result = result.drop_duplicates(subset=["contract_no"], keep="first")

    # 列順序を整える
    col_order = [c for c in CANONICAL_COLS if c in result.columns]
    result = result[col_order]

    out_path = OUTPUT_DIR / "cleaned_contracts_202401.csv"
    result.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n[OK] クレンジング完了: {len(result)} 行 -> {out_path}")
    print(f"     source_file 種類: {result['source_file'].nunique()}")
    if "renewal_status" in result.columns:
        print(f"     renewal_status 内訳:\n{result['renewal_status'].value_counts().to_string()}")
else:
    print("[FAIL] 処理対象CSVが見つかりませんでした")
    print(f"       data/ ディレクトリを確認: {DATA_DIR}")

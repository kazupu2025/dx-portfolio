import pandas as pd
import re
from pathlib import Path

BASE = Path(__file__).parent.parent
OUTPUT_DIR = Path(__file__).parent
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    "日付": "date", "Date": "date", "受付日": "date",
    "問い合わせID": "inquiry_id", "InquiryID": "inquiry_id", "案件番号": "inquiry_id",
    "担当者": "agent", "Agent": "agent", "担当": "agent",
    "エリア": "area", "Area": "area", "地区": "area",
    "物件種別": "property_type", "PropertyType": "property_type", "種別": "property_type",
    "問い合わせ経路": "channel", "Channel": "channel", "媒体": "channel",
    "ステータス": "status", "Status": "status", "進捗": "status",
    "成約フラグ": "is_contracted", "IsContracted": "is_contracted", "契約済": "is_contracted",
    "成約金額(万円)": "contract_amount", "ContractAmount": "contract_amount", "契約額": "contract_amount",
}

STAGE_MAP = {
    "問い合わせ": "問い合わせ", "inquiry": "問い合わせ", "Inquiry": "問い合わせ",
    "内見": "内見", "viewing": "内見", "Viewing": "内見",
    "申し込み": "申し込み", "application": "申し込み", "Application": "申し込み",
    "成約": "成約", "contracted": "成約", "Contracted": "成約", "contract": "成約",
}

KEEP_COLS = {
    "date", "inquiry_id", "agent", "area", "property_type",
    "channel", "status", "is_contracted", "contract_amount",
    "amount_imputed", "source_file",
}

log_lines = ["# クレンジングログ\n"]


def extract_area(filename: str) -> str:
    m = re.search(r'[ぁ-鿿々ー]+[区市町村]', filename)
    if m:
        return m.group(0)
    parts = re.split(r'[_\-\s]', Path(filename).stem)
    for part in parts:
        if re.search(r'[ぁ-鿿々ー]{2,}', part):
            return part
    return Path(filename).stem


def read_file(f: Path) -> pd.DataFrame:
    raw_bytes = f.read_bytes()
    enc = "utf-8-sig"
    for candidate in ["utf-8-sig", "utf-8", "cp932"]:
        try:
            raw_bytes.decode(candidate)
            enc = candidate
            break
        except Exception:
            continue
    return pd.read_csv(f, encoding=enc)


def normalize_date(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s in ("", "NULL", "N/A"):
        return None
    for fmt in ["%Y/%m/%d", "%Y-%m-%d", "%Y年%m月%d日"]:
        try:
            return pd.to_datetime(s, format=fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    try:
        return pd.to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        return None


all_frames = []
files = sorted(BASE.glob("*.csv"))

for f in files:
    if "output" in str(f).lower():
        continue
    area = extract_area(f.name)
    log_lines.append(f"\n## {f.name} → エリア: {area}")

    try:
        df = read_file(f)
    except Exception as e:
        log_lines.append(f"- 読み込みエラー: {e}")
        continue

    renamed = {}
    for col in df.columns:
        col_str = str(col).strip()
        if col_str in COLUMN_MAP:
            renamed[col] = COLUMN_MAP[col_str]
        elif str(col).startswith("Unnamed"):
            renamed[col] = f"_drop_{col}"
    df = df.rename(columns=renamed)

    drop_cols = [c for c in df.columns if str(c).startswith("_drop_")]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    df = df.dropna(how="all")

    if "date" in df.columns:
        df["date"] = df["date"].apply(normalize_date)
        df = df.dropna(subset=["date"])

    if "status" in df.columns:
        df["status"] = df["status"].map(lambda x: STAGE_MAP.get(str(x).strip(), str(x).strip()) if pd.notna(x) else "問い合わせ")
    else:
        df["status"] = "問い合わせ"

    if "is_contracted" in df.columns:
        df["is_contracted"] = pd.to_numeric(df["is_contracted"], errors="coerce").fillna(0).astype(int)
    else:
        df["is_contracted"] = (df["status"] == "成約").astype(int)

    df["amount_imputed"] = False
    if "contract_amount" in df.columns:
        df["contract_amount"] = pd.to_numeric(df["contract_amount"], errors="coerce")
        missing = df["contract_amount"].isna() & (df["is_contracted"] == 1)
        df.loc[missing, "amount_imputed"] = True
        df["contract_amount"] = df["contract_amount"].fillna(0)
    else:
        df["contract_amount"] = 0.0
        df["amount_imputed"] = False

    df["area"] = area
    df["source_file"] = f.name

    keep = [c for c in KEEP_COLS if c in df.columns]
    df = df[keep]

    all_frames.append(df)
    log_lines.append(f"- 完了: {len(df)} 行, 成約: {df['is_contracted'].sum()} 件")

if all_frames:
    result = pd.concat(all_frames, ignore_index=True)
    result = result.drop_duplicates()

    col_order = [
        "date", "inquiry_id", "agent", "area", "property_type",
        "channel", "status", "is_contracted", "contract_amount",
        "amount_imputed", "source_file",
    ]
    result = result[[c for c in col_order if c in result.columns]]

    result.to_csv(OUTPUT_DIR / "cleaned_inquiry_202401.csv", index=False, encoding="utf-8-sig")
    (OUTPUT_DIR / "cleansing_log.md").write_text("\n".join(log_lines), encoding="utf-8")
    total_contracts = int(result["is_contracted"].sum())
    conv_rate = total_contracts / len(result) * 100
    print(f"完了: {len(result)} 行, 成約: {total_contracts}件, 成約率: {conv_rate:.1f}%")
    print("列:", list(result.columns))
else:
    print("処理対象ファイルが見つかりませんでした")

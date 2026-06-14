import pandas as pd
import re
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    "日付": "date", "Date": "date", "申請日": "date",
    "社員ID": "employee_id", "EmployeeID": "employee_id", "社員番号": "employee_id",
    "氏名": "employee_name", "Name": "employee_name", "申請者": "employee_name",
    "部門": "department", "Department": "department", "所属部門": "department",
    "費目": "expense_type", "ExpenseType": "expense_type", "経費区分": "expense_type",
    "金額": "amount", "Amount": "amount", "申請金額": "amount",
    "予算": "budget", "Budget": "budget", "予算額": "budget",
    "領収書番号": "receipt_no", "ReceiptNo": "receipt_no", "領収No": "receipt_no",
}

KEEP_COLS = {
    "date", "employee_id", "employee_name", "department",
    "expense_type", "amount", "budget", "receipt_no",
    "amount_imputed", "source_file",
}

log_lines = ["# クレンジングログ\n"]


def extract_department(filename: str) -> str:
    m = re.search(r'[ぁ-鿿々ー]+部', filename)
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


def normalize_numeric(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s in ("-", "--", "NULL", "N/A", "NA", "none", ""):
        return None
    s = (s.replace(",", "").replace("，", "").replace("¥", "").replace("円", "").strip())
    s = s.translate(str.maketrans("０１２３４５６７８９．", "0123456789."))
    try:
        return float(s)
    except ValueError:
        return None


def normalize_date(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s in ("", "NULL", "N/A"):
        return None
    for fmt in ["%Y/%m/%d", "%Y-%m-%d", "%Y年%m月%d日", "%m/%d/%Y"]:
        try:
            return pd.to_datetime(s, format=fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    try:
        return pd.to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        return None


all_frames = []
files = sorted(Path(".").glob("*.csv"))

for f in files:
    if "output" in str(f).lower():
        continue
    dept = extract_department(f.name)
    log_lines.append(f"\n## {f.name} → 部門名: {dept}")

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

    for col in ["amount", "budget"]:
        if col in df.columns:
            df[col] = df[col].apply(normalize_numeric)
            if col == "amount":
                df["amount_imputed"] = df[col].isna()
                df[col] = df[col].fillna(0)
            else:
                df[col] = df[col].fillna(0)

    df["department"] = dept
    df["source_file"] = f.name

    keep = [c for c in KEEP_COLS if c in df.columns]
    df = df[keep]

    all_frames.append(df)
    log_lines.append(f"- 完了: {len(df)} 行")

if all_frames:
    result = pd.concat(all_frames, ignore_index=True)

    for col in ["amount", "budget"]:
        if col not in result.columns:
            result[col] = 0
        result[col] = result[col].fillna(0)

    if "amount_imputed" in result.columns:
        result["amount_imputed"] = result["amount_imputed"].fillna(False).astype(bool)
    else:
        result["amount_imputed"] = False

    result = result.drop_duplicates()

    col_order = [
        "date", "employee_id", "employee_name", "department",
        "expense_type", "amount", "budget", "receipt_no",
        "amount_imputed", "source_file",
    ]
    result = result[[c for c in col_order if c in result.columns]]

    result.to_csv(OUTPUT_DIR / "cleaned_expense_202401.csv", index=False, encoding="utf-8-sig")
    (OUTPUT_DIR / "cleansing_log.md").write_text("\n".join(log_lines), encoding="utf-8")
    print(f"完了: {len(result)} 行, {result['department'].nunique()} 部門")
    print("列:", list(result.columns))
else:
    print("処理対象ファイルが見つかりませんでした")

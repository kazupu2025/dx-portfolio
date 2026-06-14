import pandas as pd
import re
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMN_MAP = {
    "日付": "date", "Date": "date", "検査日": "date",
    "製品コード": "product_code", "ProductCode": "product_code", "品番": "product_code",
    "製品名": "product_name", "ProductName": "product_name", "製品": "product_name",
    "工程": "process", "Process": "process", "工程名": "process",
    "ロットNo": "lot_no", "LotNo": "lot_no", "ロット番号": "lot_no",
    "検査値": "inspection_value", "InspectionValue": "inspection_value", "計測値": "inspection_value",
    "下限値": "lower_limit", "LowerLimit": "lower_limit", "規格下限": "lower_limit",
    "上限値": "upper_limit", "UpperLimit": "upper_limit", "規格上限": "upper_limit",
    "単位": "unit", "Unit": "unit",
    "検査員": "inspector", "Inspector": "inspector", "担当者": "inspector",
    "判定": "result", "Result": "result", "合否": "result",
}

KEEP_COLS = {
    "date", "product_code", "product_name", "process", "lot_no",
    "inspection_value", "lower_limit", "upper_limit", "unit",
    "inspector", "result", "is_defect", "value_imputed", "source_file",
}

log_lines = ["# クレンジングログ\n"]


def extract_process(filename: str) -> str:
    m = re.search(r'[ぁ-鿿々ー]+(工程|検査)', filename)
    if m:
        return m.group(0)
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


def normalize_numeric(val):
    if pd.isna(val):
        return None
    s = str(val).strip().replace(",", "").replace("，", "")
    s = s.translate(str.maketrans("０１２３４５６７８９．", "0123456789."))
    try:
        return float(s)
    except ValueError:
        return None


all_frames = []
files = sorted(Path(".").glob("*.csv"))

for f in files:
    if "output" in str(f).lower():
        continue
    process = extract_process(f.name)
    log_lines.append(f"\n## {f.name} → 工程: {process}")

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

    df["value_imputed"] = False
    for col in ["inspection_value", "lower_limit", "upper_limit"]:
        if col in df.columns:
            df[col] = df[col].apply(normalize_numeric)
            if col == "inspection_value":
                missing = df[col].isna()
                df.loc[missing, "value_imputed"] = True
                # 中央値で補完
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val if median_val is not None else 0)

    # is_defect: 規格外 OR result=="NG"
    if "inspection_value" in df.columns and "lower_limit" in df.columns and "upper_limit" in df.columns:
        df["is_defect"] = (
            (df["inspection_value"] < df["lower_limit"]) |
            (df["inspection_value"] > df["upper_limit"])
        )
    elif "result" in df.columns:
        df["is_defect"] = df["result"].str.upper() == "NG"
    else:
        df["is_defect"] = False

    # result列の正規化
    if "result" in df.columns:
        df["result"] = df["result"].str.upper().apply(
            lambda x: "OK" if x in ("OK", "合格", "PASS") else ("NG" if x in ("NG", "不合格", "FAIL") else x)
        )
    else:
        df["result"] = df["is_defect"].map({True: "NG", False: "OK"})

    df["process"] = process
    df["source_file"] = f.name

    keep = [c for c in KEEP_COLS if c in df.columns]
    df = df[keep]

    all_frames.append(df)
    log_lines.append(f"- 完了: {len(df)} 行, 不良: {df['is_defect'].sum()} 件")

if all_frames:
    result = pd.concat(all_frames, ignore_index=True)
    result = result.drop_duplicates()

    col_order = [
        "date", "product_code", "product_name", "process", "lot_no",
        "inspection_value", "lower_limit", "upper_limit", "unit",
        "inspector", "result", "is_defect", "value_imputed", "source_file",
    ]
    result = result[[c for c in col_order if c in result.columns]]

    result.to_csv(OUTPUT_DIR / "cleaned_inspection_202401.csv", index=False, encoding="utf-8-sig")
    (OUTPUT_DIR / "cleansing_log.md").write_text("\n".join(log_lines), encoding="utf-8")
    total_defects = result["is_defect"].sum()
    defect_rate = total_defects / len(result) * 100
    print(f"完了: {len(result)} 行, 不良率: {defect_rate:.2f}% ({total_defects}件)")
    print("列:", list(result.columns))
else:
    print("処理対象ファイルが見つかりませんでした")
